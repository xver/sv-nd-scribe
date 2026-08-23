/**
 * SV ND Scribe - VS Code Extension
 * Provides real-time in-editor diagnostics and Quick Fix code actions for SystemVerilog files.
 */
const vscode = require('vscode');
const child_process = require('child_process');

let diagnosticCollection;
let statusDiagnosticCollection;

// Rules marked unsafe / report-only in agent YAML configs – no actionable
// auto-fix exists, so we suppress the QuickFix lightbulb for these.
const UNFIXABLE_RULES = new Set([
    'WKL-001', // class member prefix  (semantic rename)
    'WKL-002', // typedef suffix       (semantic rename)
    'WKL-003', // macro format         (semantic rename)
    'WKL-004', // interface naming     (semantic rename)
    'WKL-007', // line length          (structural reflow)
]);

class SvScribeCodeActionProvider {
    provideCodeActions(document, range, context, token) {
        const config = vscode.workspace.getConfiguration('sv-nd-scribe');
        if (config.get('enableQuickFix') === false) {
            return [];
        }

        const actions = [];
        const seenRules = new Set();

        for (const diagnostic of context.diagnostics) {
            if (diagnostic.source !== 'sv-nd-scribe') {
                continue;
            }

            const rawRuleId = diagnostic.code ? String(diagnostic.code) : '';
            const cleanRuleId = rawRuleId.replace(/[\[\]]/g, '').trim();

            // Skip rules that have no actionable auto-fix
            if (UNFIXABLE_RULES.has(cleanRuleId)) {
                continue;
            }

            if (cleanRuleId && !seenRules.has(cleanRuleId)) {
                seenRules.add(cleanRuleId);

                const action = new vscode.CodeAction(
                    `SV Scribe: Fix [${cleanRuleId}]`,
                    vscode.CodeActionKind.QuickFix
                );
                action.command = {
                    command: 'sv-nd-scribe.fixRule',
                    title: `SV Scribe: Fix [${cleanRuleId}]`,
                    arguments: [document.uri, cleanRuleId]
                };
                action.diagnostics = [diagnostic];
                action.isPreferred = true;
                actions.push(action);
            }
        }

        // If there are diagnostics in the file, also offer "Fix all auto-fixable issues in file"
        const allDocDiagnostics = diagnosticCollection ? diagnosticCollection.get(document.uri) || [] : [];
        if (allDocDiagnostics.length > 0) {
            const fixAllAction = new vscode.CodeAction(
                'SV Scribe: Fix all auto-fixable issues in file',
                vscode.CodeActionKind.SourceFixAll
            );
            fixAllAction.command = {
                command: 'sv-nd-scribe.fix',
                title: 'SV Scribe: Fix all auto-fixable issues in file',
                arguments: [document.uri]
            };
            actions.push(fixAllAction);
        }

        return actions;
    }
}

function activate(context) {
    diagnosticCollection = vscode.languages.createDiagnosticCollection('sv-nd-scribe');
    context.subscriptions.push(diagnosticCollection);
    statusDiagnosticCollection = vscode.languages.createDiagnosticCollection('sv-nd-scribe-status');
    context.subscriptions.push(statusDiagnosticCollection);

    // Register Quick Fix CodeAction Provider
    const documentSelector = [
        { language: 'systemverilog', scheme: 'file' },
        { language: 'verilog', scheme: 'file' },
        { language: 'systemverilog', scheme: 'untitled' },
        { language: 'verilog', scheme: 'untitled' }
    ];
    context.subscriptions.push(
        vscode.languages.registerCodeActionsProvider(
            documentSelector,
            new SvScribeCodeActionProvider(),
            {
                providedCodeActionKinds: [
                    vscode.CodeActionKind.QuickFix,
                    vscode.CodeActionKind.SourceFixAll
                ]
            }
        )
    );

    // Lint active editor on startup if one is active
    if (vscode.window.activeTextEditor) {
        lintDocument(vscode.window.activeTextEditor.document);
    }

    // Trigger on document open (if configured)
    context.subscriptions.push(
        vscode.workspace.onDidOpenTextDocument((document) => {
            const config = vscode.workspace.getConfiguration('sv-nd-scribe');
            if (config.get('runOn') === 'onOpen') {
                lintDocument(document);
            }
        })
    );

    // Trigger on save (always active)
    context.subscriptions.push(
        vscode.workspace.onDidSaveTextDocument((document) => {
            lintDocument(document);
        })
    );

    // Trigger when changing active editor
    context.subscriptions.push(
        vscode.window.onDidChangeActiveTextEditor((editor) => {
            if (editor) {
                lintDocument(editor.document);
            }
        })
    );

    // Clear diagnostics on document close
    context.subscriptions.push(
        vscode.workspace.onDidCloseTextDocument((document) => {
            diagnosticCollection.delete(document.uri);
            if (statusDiagnosticCollection) {
                statusDiagnosticCollection.delete(document.uri);
            }
        })
    );

    // Register manual commands
    context.subscriptions.push(
        vscode.commands.registerCommand('sv-nd-scribe.lint', () => {
            if (vscode.window.activeTextEditor) {
                lintDocument(vscode.window.activeTextEditor.document);
            } else {
                vscode.window.showInformationMessage('No active text editor to lint.');
            }
        })
    );

    context.subscriptions.push(
        vscode.commands.registerCommand('sv-nd-scribe.clear', () => {
            if (vscode.window.activeTextEditor) {
                const uri = vscode.window.activeTextEditor.document.uri;
                diagnosticCollection.set(uri, []);
            }
            if (statusDiagnosticCollection) {
                statusDiagnosticCollection.clear();
            }
        })
    );

    context.subscriptions.push(
        vscode.commands.registerCommand('sv-nd-scribe.lintAll', () => {
            const svDocs = vscode.workspace.textDocuments.filter(doc => 
                doc.languageId === 'systemverilog' || doc.languageId === 'verilog'
            );
            
            if (svDocs.length > 0) {
                lintFiles(svDocs);
                vscode.window.showInformationMessage(`Linting ${svDocs.length} SystemVerilog document(s)...`);
            } else {
                vscode.window.showInformationMessage('No open SystemVerilog documents to lint.');
            }
        })
    );

    // Register fix commands
    context.subscriptions.push(
        vscode.commands.registerCommand('sv-nd-scribe.fix', async (targetUri) => {
            await runFixer(targetUri);
        })
    );

    context.subscriptions.push(
        vscode.commands.registerCommand('sv-nd-scribe.fixRule', async (targetUri, ruleId) => {
            await runFixer(targetUri, ruleId);
        })
    );

    const getErrorUri = () => {
        if (vscode.window.activeTextEditor) {
            return vscode.window.activeTextEditor.document.uri;
        }
        const svDocs = vscode.workspace.textDocuments.filter(doc => 
            doc.languageId === 'systemverilog' || doc.languageId === 'verilog'
        );
        if (svDocs.length > 0) {
            return svDocs[0].uri;
        }
        if (vscode.workspace.workspaceFolders && vscode.workspace.workspaceFolders.length > 0) {
            const path = require('path');
            const fs = require('fs');
            const rootPath = vscode.workspace.workspaceFolders[0].uri.fsPath;
            const packageJsonPath = path.join(rootPath, 'vscode', 'package.json');
            if (fs.existsSync(packageJsonPath)) {
                return vscode.Uri.file(packageJsonPath);
            }
            const readmePath = path.join(rootPath, 'README.md');
            if (fs.existsSync(readmePath)) {
                return vscode.Uri.file(readmePath);
            }
            return vscode.workspace.workspaceFolders[0].uri;
        }
        return vscode.Uri.parse('sv-nd-scribe-status://error');
    };

    const statusHandler = (isStartup = false) => {
        statusDiagnosticCollection.clear();
        const diagnostics = [];

        const config = vscode.workspace.getConfiguration('sv-nd-scribe');
        const pythonPath = config.get('pythonPath') || 'python3';
        const linterPath = getLinterPath();
        const scribeHome = getScribeHome();

        if (!scribeHome && !process.env.SVND_SCRIBE_HOME) {
            const msg = 'SV ND Scribe Status: Error: SVND_SCRIBE_HOME could not be resolved.';
            vscode.window.showErrorMessage(msg);
            diagnostics.push(new vscode.Diagnostic(
                new vscode.Range(0, 0, 0, 100),
                msg,
                vscode.DiagnosticSeverity.Error
            ));
            diagnostics.forEach(d => d.source = 'sv-nd-scribe-status');
            statusDiagnosticCollection.set(getErrorUri(), diagnostics);
            return;
        }

        if (!linterPath) {
            const msg = 'SV ND Scribe: linterPath could not be resolved.';
            vscode.window.showErrorMessage(msg);
            diagnostics.push(new vscode.Diagnostic(
                new vscode.Range(0, 0, 0, 100),
                msg,
                vscode.DiagnosticSeverity.Error
            ));
            diagnostics.forEach(d => d.source = 'sv-nd-scribe-status');
            statusDiagnosticCollection.set(getErrorUri(), diagnostics);
            return;
        }

        const env = getExecutionEnv(scribeHome);

        child_process.execFile(pythonPath, [linterPath, '--status'], { env }, (error, stdout, stderr) => {
            if (error) {
                const msg = `SV ND Scribe Status: Error: ${stdout.trim() || stderr.trim() || error.message}`;
                vscode.window.showErrorMessage(msg);
                diagnostics.push(new vscode.Diagnostic(
                    new vscode.Range(0, 0, 0, 100),
                    msg,
                    vscode.DiagnosticSeverity.Error
                ));
            } else {
                if (!isStartup) {
                    vscode.window.showInformationMessage(`SV ND Scribe Status: ${stdout.trim()}`);
                }
            }
            if (diagnostics.length > 0) {
                diagnostics.forEach(d => d.source = 'sv-nd-scribe-status');
                statusDiagnosticCollection.set(getErrorUri(), diagnostics);
            }
        });
    };

    context.subscriptions.push(vscode.commands.registerCommand('sv-nd-scribe.status', () => statusHandler(false)));
    context.subscriptions.push(vscode.commands.registerCommand('sv-nd-scribe.verifyInstallation', () => statusHandler(false)));

    // Perform wake-up status check on startup
    statusHandler(true);
}

function lintDocument(document) {
    if (document.languageId !== 'systemverilog' && document.languageId !== 'verilog') {
        return;
    }
    lintFiles([document]);
}

function lintFiles(documents) {
    if (documents.length === 0) return;

    const config = vscode.workspace.getConfiguration('sv-nd-scribe');
    const pythonPath = config.get('pythonPath') || 'python3';
    const linterPath = getLinterPath();
    
    if (!linterPath) {
        return;
    }

    const filePaths = documents.map(doc => doc.uri.fsPath);
    const env = getExecutionEnv();
    
    // Execute linter process
    child_process.execFile(pythonPath, [linterPath, ...filePaths], { env }, (error, stdout, stderr) => {
        const diagnosticsMap = new Map();
        const lines = stdout.split('\n');
        
        // Matches output: <file>:<line>: [<severity>] [<rule_id>] <message>
        const lineRegex = /^(.*?):(\d+): \[(ERROR|WARNING|INFO)\]\s+(\[[^\]]+\])\s+(.*)$/;

        for (const line of lines) {
            const match = lineRegex.exec(line.trim());
            if (match) {
                const file = match[1];
                const lineNum = parseInt(match[2], 10) - 1; // VS Code API is 0-indexed for lines
                const severityStr = match[3];
                const ruleId = match[4];
                const message = match[5];

                let severity = vscode.DiagnosticSeverity.Error;
                if (severityStr === 'WARNING') {
                    severity = vscode.DiagnosticSeverity.Warning;
                } else if (severityStr === 'INFO') {
                    severity = vscode.DiagnosticSeverity.Information;
                }

                // Determine diagnostic range (underline the entire line, ignoring leading/trailing whitespaces)
                const targetUri = vscode.Uri.file(file);
                const targetKey = targetUri.toString();
                
                const targetDoc = documents.find(doc => doc.uri.toString() === targetKey);
                let lineText = '';
                if (targetDoc && lineNum >= 0 && lineNum < targetDoc.lineCount) {
                    lineText = targetDoc.lineAt(lineNum).text;
                }
                
                const startChar = lineText.length - lineText.trimStart().length;
                const endChar = lineText.length;
                const range = new vscode.Range(lineNum, startChar, lineNum, endChar > 0 ? endChar : 100);

                const diagnostic = new vscode.Diagnostic(range, `${ruleId}: ${message}`, severity);
                diagnostic.code = ruleId;
                diagnostic.source = 'sv-nd-scribe';

                if (!diagnosticsMap.has(targetKey)) {
                    diagnosticsMap.set(targetKey, []);
                }
                diagnosticsMap.get(targetKey).push(diagnostic);
            }
        }

        // Reset diagnostics for all these documents
        for (const doc of documents) {
            diagnosticCollection.set(doc.uri, []);
        }
        
        // Apply diagnostics
        for (const [uriStr, diagList] of diagnosticsMap.entries()) {
            diagnosticCollection.set(vscode.Uri.parse(uriStr), diagList);
        }
    });
}

async function runFixer(targetUri, ruleId) {
    let uri = targetUri;
    if (!uri && vscode.window.activeTextEditor) {
        uri = vscode.window.activeTextEditor.document.uri;
    }
    if (!uri) {
        vscode.window.showInformationMessage('No active SystemVerilog document to fix.');
        return;
    }

    try {
        const document = await vscode.workspace.openTextDocument(uri);
        if (document.isDirty) {
            await document.save();
        }
    } catch (e) {
        // Document might already be on disk or not loaded
    }

    const config = vscode.workspace.getConfiguration('sv-nd-scribe');
    const pythonPath = config.get('pythonPath') || 'python3';
    const scribeHome = getScribeHome();
    const env = getExecutionEnv(scribeHome);

    const filePath = uri.fsPath;
    const args = ['-m', 'agent', filePath, '--batch', '--no-backup'];
    if (ruleId) {
        const cleanRuleId = ruleId.replace(/[\[\]]/g, '').trim();
        args.push('--rules', cleanRuleId);
    }

    const execOptions = { env };
    if (scribeHome) {
        execOptions.cwd = scribeHome;
    }

    child_process.execFile(pythonPath, args, execOptions, async (error, stdout, stderr) => {
        // Note: ScribeAgent returns 0 on complete clean or 2 on remaining violations.
        // Fatal failures exit with other non-zero codes (like 1).
        if (error && error.code !== 0 && error.code !== 2) {
            const msg = (stderr && stderr.trim()) || (stdout && stdout.trim()) || error.message;
            vscode.window.showErrorMessage(`SV Scribe Fix Error: ${msg}`);
            return;
        }

        try {
            // Reload the document directly from disk so VS Code synchronizes
            // without marking the buffer dirty or triggering a file save conflict.
            const activeEditor = vscode.window.activeTextEditor;
            if (activeEditor && activeEditor.document.uri.toString() === uri.toString()) {
                await vscode.commands.executeCommand('workbench.action.files.revert');
                lintDocument(activeEditor.document);
            } else {
                const doc = await vscode.workspace.openTextDocument(uri);
                lintDocument(doc);
            }
        } catch (e) {
            // Fallback: re-lint open document
            const targetDoc = vscode.workspace.textDocuments.find(d => d.uri.toString() === uri.toString());
            if (targetDoc) {
                lintDocument(targetDoc);
            }
        }

        const ruleDesc = ruleId ? `rule [${ruleId.replace(/[\[\]]/g, '')}]` : 'auto-fixable issues';
        vscode.window.setStatusBarMessage(`SV Scribe: Applied fix for ${ruleDesc}`, 4000);
    });
}

function getExecutionEnv(providedHome) {
    const config = vscode.workspace.getConfiguration('sv-nd-scribe');
    const customEnv = config.get('env') || {};
    const path = require('path');
    
    const env = { ...process.env };
    const scribeHome = providedHome || getScribeHome();
    
    if (scribeHome) {
        env.SVND_SCRIBE_HOME = scribeHome;
        env.PYTHONPATH = scribeHome + (process.env.PYTHONPATH ? path.delimiter + process.env.PYTHONPATH : '');
        env.SV_ND_SCRIBE_PROJECT_CONFIG = path.join(scribeHome, 'linter', 'configs');
    }
    
    // Apply user-specified custom env entries with ${workspaceFolder} substitution
    for (const [key, value] of Object.entries(customEnv)) {
        if (value !== undefined && value !== null) {
            let strVal = String(value);
            if (scribeHome) {
                strVal = strVal.replace(/\${workspaceFolder}/g, scribeHome);
            }
            env[key] = strVal;
        }
    }
    
    return env;
}

function getScribeHome() {
    const config = vscode.workspace.getConfiguration('sv-nd-scribe');
    const configuredAgent = config.get('agentPath');
    const path = require('path');
    const fs = require('fs');

    if (configuredAgent && fs.existsSync(configuredAgent)) {
        try {
            const stat = fs.statSync(configuredAgent);
            return stat.isDirectory() ? configuredAgent : path.dirname(path.dirname(configuredAgent));
        } catch (e) {
            // ignore
        }
    }

    const linterPath = getLinterPath();
    if (linterPath) {
        return path.dirname(path.dirname(linterPath));
    }

    if (process.env.SVND_SCRIBE_HOME) {
        return process.env.SVND_SCRIBE_HOME;
    }

    if (vscode.workspace.workspaceFolders && vscode.workspace.workspaceFolders.length > 0) {
        return vscode.workspace.workspaceFolders[0].uri.fsPath;
    }

    return null;
}

function getLinterPath() {
    const config = vscode.workspace.getConfiguration('sv-nd-scribe');
    let linterPath = config.get('linterPath');
    if (!linterPath && process.env.SVND_SCRIBE_HOME) {
        const path = require('path');
        linterPath = path.join(process.env.SVND_SCRIBE_HOME, 'linter', 'linter.py');
    }
    return linterPath;
}

function deactivate() {
    if (diagnosticCollection) {
        diagnosticCollection.clear();
    }
    if (statusDiagnosticCollection) {
        statusDiagnosticCollection.clear();
    }
}

module.exports = {
    activate,
    deactivate,
    SvScribeCodeActionProvider
};

