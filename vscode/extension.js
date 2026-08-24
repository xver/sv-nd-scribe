/**
 * SV ND Scribe - VS Code Extension
 * Provides real-time in-editor diagnostics and Quick Fix code actions for SystemVerilog files.
 */
const vscode = require('vscode');
const child_process = require('child_process');
const path = require('path');
const fs = require('fs');

let diagnosticCollection;
let statusDiagnosticCollection;
let outputChannel;

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
        let hasHeaderDiagnostic = false;

        for (const diagnostic of context.diagnostics) {
            if (diagnostic.source !== 'sv-nd-scribe') {
                continue;
            }

            const rawRuleId = diagnostic.code ? String(diagnostic.code) : '';
            const cleanRuleId = rawRuleId.replace(/[\[\]]/g, '').trim();

            if (cleanRuleId === 'ND-001') {
                hasHeaderDiagnostic = true;
            }

            if (cleanRuleId && !seenRules.has(cleanRuleId)) {
                seenRules.add(cleanRuleId);

                if (cleanRuleId === 'ND-001') {
                    const action = new vscode.CodeAction(
                        'SV Scribe: Fix [ND-001] (File Header)',
                        vscode.CodeActionKind.QuickFix
                    );
                    action.command = {
                        command: 'sv-nd-scribe.fixRule',
                        title: 'SV Scribe: Fix [ND-001]',
                        arguments: [document.uri, 'ND-001']
                    };
                    action.diagnostics = [diagnostic];
                    action.isPreferred = true;
                    actions.push(action);

                    const overwriteAction = new vscode.CodeAction(
                        'SV Scribe: Overwrite File Header from Template',
                        vscode.CodeActionKind.QuickFix
                    );
                    overwriteAction.command = {
                        command: 'sv-nd-scribe.overwriteHeaderFromTemplate',
                        title: 'SV Scribe: Overwrite File Header from Template',
                        arguments: [document.uri]
                    };
                    overwriteAction.diagnostics = [diagnostic];
                    actions.push(overwriteAction);

                    const openTmplAction = new vscode.CodeAction(
                        'SV Scribe: Open Header Template to Edit (header_template.txt)',
                        vscode.CodeActionKind.QuickFix
                    );
                    openTmplAction.command = {
                        command: 'sv-nd-scribe.openHeaderTemplate',
                        title: 'SV Scribe: Open Header Template to Edit',
                        arguments: [document.uri]
                    };
                    openTmplAction.diagnostics = [diagnostic];
                    actions.push(openTmplAction);

                    const resetTmplAction = new vscode.CodeAction(
                        'SV Scribe: Reset Header Template to Default',
                        vscode.CodeActionKind.QuickFix
                    );
                    resetTmplAction.command = {
                        command: 'sv-nd-scribe.resetHeaderTemplate',
                        title: 'SV Scribe: Reset Header Template to Default',
                        arguments: [document.uri]
                    };
                    resetTmplAction.diagnostics = [diagnostic];
                    actions.push(resetTmplAction);
                    continue;
                }

                // Skip rules that have no actionable auto-fix
                if (UNFIXABLE_RULES.has(cleanRuleId)) {
                    continue;
                }

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

        // Whenever cursor is in header region (top 30 lines) or header actions are requested:
        // Always provide Overwrite, Open, and Reset template options
        if (!hasHeaderDiagnostic && range.start.line <= 30) {
            const overwriteAction = new vscode.CodeAction(
                'SV Scribe: Overwrite File Header from Template',
                vscode.CodeActionKind.QuickFix
            );
            overwriteAction.command = {
                command: 'sv-nd-scribe.overwriteHeaderFromTemplate',
                title: 'SV Scribe: Overwrite File Header from Template',
                arguments: [document.uri]
            };
            actions.push(overwriteAction);

            const openTmplAction = new vscode.CodeAction(
                'SV Scribe: Open Header Template to Edit (header_template.txt)',
                vscode.CodeActionKind.QuickFix
            );
            openTmplAction.command = {
                command: 'sv-nd-scribe.openHeaderTemplate',
                title: 'SV Scribe: Open Header Template to Edit',
                arguments: [document.uri]
            };
            actions.push(openTmplAction);

            const resetTmplAction = new vscode.CodeAction(
                'SV Scribe: Reset Header Template to Default',
                vscode.CodeActionKind.QuickFix
            );
            resetTmplAction.command = {
                command: 'sv-nd-scribe.resetHeaderTemplate',
                title: 'SV Scribe: Reset Header Template to Default',
                arguments: [document.uri]
            };
            actions.push(resetTmplAction);
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
    outputChannel = vscode.window.createOutputChannel('SV ND Scribe');
    context.subscriptions.push(outputChannel);

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

    // Trigger on active editor change
    context.subscriptions.push(
        vscode.window.onDidChangeActiveTextEditor((editor) => {
            if (editor) {
                lintDocument(editor.document);
            }
        })
    );

    // Trigger on document open
    context.subscriptions.push(
        vscode.workspace.onDidOpenTextDocument((document) => {
            lintDocument(document);
        })
    );

    // Trigger on save
    context.subscriptions.push(
        vscode.workspace.onDidSaveTextDocument((document) => {
            lintDocument(document);
        })
    );

    // Clear diagnostics when a document is closed
    context.subscriptions.push(
        vscode.workspace.onDidCloseTextDocument((document) => {
            diagnosticCollection.delete(document.uri);
        })
    );

    // Register commands for linting
    context.subscriptions.push(
        vscode.commands.registerCommand('sv-nd-scribe.lint', () => {
            const editor = vscode.window.activeTextEditor;
            if (editor) {
                lintDocument(editor.document);
            }
        })
    );

    context.subscriptions.push(
        vscode.commands.registerCommand('sv-nd-scribe.lintActive', () => {
            const editor = vscode.window.activeTextEditor;
            if (editor) {
                lintDocument(editor.document);
            } else {
                vscode.window.showInformationMessage('No active SystemVerilog editor to lint.');
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
            } else {
                vscode.window.showInformationMessage('No open SystemVerilog documents to lint.');
            }
        })
    );

    context.subscriptions.push(
        vscode.commands.registerCommand('sv-nd-scribe.clear', () => {
            diagnosticCollection.clear();
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

    context.subscriptions.push(
        vscode.commands.registerCommand('sv-nd-scribe.openHeaderTemplate', async (targetUri) => {
            try {
                let templateUri = null;
                const wsFolders = vscode.workspace.workspaceFolders;
                if (wsFolders && wsFolders.length > 0) {
                    for (const folder of wsFolders) {
                        const cand1 = vscode.Uri.joinPath(folder.uri, '.sv-nd-scribe', 'header_template.txt');
                        const cand2 = vscode.Uri.joinPath(folder.uri, 'agent', 'templates', 'header_template.txt');
                        const cand3 = vscode.Uri.joinPath(folder.uri, 'header_template.txt');
                        try {
                            await vscode.workspace.fs.stat(cand1);
                            templateUri = cand1;
                            break;
                        } catch (e) {}
                        try {
                            await vscode.workspace.fs.stat(cand2);
                            templateUri = cand2;
                            break;
                        } catch (e) {}
                        try {
                            await vscode.workspace.fs.stat(cand3);
                            templateUri = cand3;
                            break;
                        } catch (e) {}
                    }
                    if (!templateUri) {
                        templateUri = vscode.Uri.joinPath(wsFolders[0].uri, 'agent', 'templates', 'header_template.txt');
                    }
                }
                if (!templateUri) {
                    const scribeHome = getScribeHome();
                    templateUri = vscode.Uri.file(path.join(scribeHome || '', 'agent', 'templates', 'header_template.txt'));
                }
                const doc = await vscode.workspace.openTextDocument(templateUri);
                await vscode.window.showTextDocument(doc);
            } catch (err) {
                vscode.window.showErrorMessage(`SV Scribe: Could not open header_template.txt: ${err.message}`);
            }
        })
    );

    context.subscriptions.push(
        vscode.commands.registerCommand('sv-nd-scribe.overwriteHeaderFromTemplate', async (targetUri) => {
            let uri = targetUri;
            if (!uri && vscode.window.activeTextEditor) {
                uri = vscode.window.activeTextEditor.document.uri;
            }
            if (!uri) return;
            await runFixer(uri, 'ND-001', ['--overwrite-header']);
        })
    );

    context.subscriptions.push(
        vscode.commands.registerCommand('sv-nd-scribe.resetHeaderTemplate', async () => {
            const pythonPath = getPythonPath();
            const scribeHome = getScribeHome();
            const env = getExecutionEnv(scribeHome);
            const execOptions = { env };
            if (scribeHome) execOptions.cwd = scribeHome;
            child_process.execFile(pythonPath, ['-m', 'agent', '--reset-header-template'], execOptions, (error, stdout, stderr) => {
                if (error) {
                    const msg = (stderr && stderr.trim()) || (stdout && stdout.trim()) || error.message;
                    vscode.window.showErrorMessage(`SV Scribe: Reset template failed: ${msg}`);
                } else {
                    vscode.window.showInformationMessage('SV Scribe: File header template reset to default.');
                    if (vscode.window.activeTextEditor) {
                        lintDocument(vscode.window.activeTextEditor.document);
                    }
                }
            });
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

        const pythonPath = getPythonPath();
        const scribeHome = getScribeHome();
        const linterPath = getLinterPath(scribeHome);

        if (!scribeHome && !process.env.SVND_SCRIBE_HOME) {
            const msg = 'SV ND Scribe Status: Error: SVND_SCRIBE_HOME could not be resolved.';
            if (!isStartup) vscode.window.showErrorMessage(msg);
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
            if (!isStartup) vscode.window.showErrorMessage(msg);
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
        const execOptions = { env };
        if (scribeHome) execOptions.cwd = scribeHome;

        child_process.execFile(pythonPath, [linterPath, '--status'], execOptions, (error, stdout, stderr) => {
            if (error) {
                const msg = `SV ND Scribe Status: Error: ${stdout.trim() || stderr.trim() || error.message}`;
                if (!isStartup) vscode.window.showErrorMessage(msg);
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
    if (!document) return;
    const lang = (document.languageId || '').toLowerCase();
    const fileName = (document.fileName || '').toLowerCase();
    
    // Check if systemverilog / verilog or ends with .sv / .svh / .v
    if (lang === 'systemverilog' || lang === 'verilog' || fileName.endsWith('.sv') || fileName.endsWith('.svh') || fileName.endsWith('.v')) {
        lintFiles([document]);
    }
}

function lintFiles(documents) {
    if (documents.length === 0) return;

    const pythonPath = getPythonPath();
    const scribeHome = getScribeHome(documents[0].uri);
    const linterPath = getLinterPath(scribeHome);
    
    if (!linterPath) {
        if (outputChannel) outputChannel.appendLine('[Error] Could not resolve linterPath');
        return;
    }

    const filePaths = documents.map(doc => doc.uri.fsPath);
    const env = getExecutionEnv(scribeHome);
    const execOptions = { env };
    if (scribeHome) {
        execOptions.cwd = scribeHome;
    }
    
    if (outputChannel) {
        outputChannel.appendLine(`[Lint] Executing ${pythonPath} ${linterPath} ${filePaths.join(' ')}`);
    }

    // Execute linter process
    child_process.execFile(pythonPath, [linterPath, ...filePaths], execOptions, (error, stdout, stderr) => {
        if (outputChannel) {
            if (stderr) outputChannel.appendLine(`[Stderr] ${stderr}`);
            outputChannel.appendLine(`[Stdout] ${stdout}`);
        }

        const diagnosticsMap = new Map();
        const lines = (stdout || '').split('\n');
        
        // Matches output: <file>:<line>: [<severity>] [<rule_id>] <message>
        const lineRegex = /^(.*?):(\d+): \[(ERROR|WARNING|INFO)\]\s+(\[[^\]]+\])\s+(.*)$/;

        for (const line of lines) {
            const match = lineRegex.exec(line.trim());
            if (match) {
                const file = match[1].trim();
                const lineNum = Math.max(0, parseInt(match[2], 10) - 1); // VS Code API is 0-indexed for lines
                const severityStr = match[3];
                const ruleId = match[4];
                const message = match[5];

                let severity = vscode.DiagnosticSeverity.Error;
                if (severityStr === 'WARNING') {
                    severity = vscode.DiagnosticSeverity.Warning;
                } else if (severityStr === 'INFO') {
                    severity = vscode.DiagnosticSeverity.Information;
                }

                // Match against open documents robustly by URI or basename
                const baseName = path.basename(file).toLowerCase();
                const targetDoc = documents.find(doc => {
                    const docBase = path.basename(doc.uri.fsPath).toLowerCase();
                    return docBase === baseName;
                }) || (documents.length === 1 ? documents[0] : null);

                const targetDocUri = targetDoc ? targetDoc.uri : vscode.Uri.file(file);
                const targetKey = targetDocUri.toString();

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
                    diagnosticsMap.set(targetKey, { uri: targetDocUri, list: [] });
                }
                diagnosticsMap.get(targetKey).list.push(diagnostic);
            }
        }

        // Reset diagnostics for all these documents
        for (const doc of documents) {
            diagnosticCollection.set(doc.uri, []);
        }
        
        // Apply diagnostics
        for (const { uri, list } of diagnosticsMap.values()) {
            diagnosticCollection.set(uri, list);
        }
    });
}

async function runFixer(targetUri, ruleId, extraArgs) {
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

    const pythonPath = getPythonPath();
    const scribeHome = getScribeHome(uri);
    const env = getExecutionEnv(scribeHome);

    const filePath = uri.fsPath;
    const args = ['-m', 'agent', filePath, '--batch', '--no-backup'];
    if (ruleId) {
        const cleanRuleId = ruleId.replace(/[\[\]]/g, '').trim();
        args.push('--rules', cleanRuleId);
    }
    if (extraArgs && Array.isArray(extraArgs)) {
        args.push(...extraArgs);
    }

    const execOptions = { env };
    if (scribeHome) {
        execOptions.cwd = scribeHome;
    }

    child_process.execFile(pythonPath, args, execOptions, async (error, stdout, stderr) => {
        if (error && error.code !== 0 && error.code !== 2) {
            const msg = (stderr && stderr.trim()) || (stdout && stdout.trim()) || error.message;
            vscode.window.showErrorMessage(`SV Scribe Fix Error: ${msg}`);
            return;
        }

        try {
            const fileBytes = await vscode.workspace.fs.readFile(uri);
            const newContent = Buffer.from(fileBytes).toString('utf-8');
            const doc = await vscode.workspace.openTextDocument(uri);
            const currentContent = doc.getText();
            if (currentContent !== newContent) {
                const edit = new vscode.WorkspaceEdit();
                const fullRange = new vscode.Range(
                    doc.positionAt(0),
                    doc.positionAt(currentContent.length)
                );
                edit.replace(uri, fullRange, newContent);
                await vscode.workspace.applyEdit(edit);
                try {
                    if (doc.isDirty) {
                        await doc.save();
                    }
                } catch (saveErr) {
                    // Safe to ignore: disk already has newContent written atomically
                }
            }
            lintDocument(doc);
        } catch (e) {
            const targetDoc = vscode.workspace.textDocuments.find(d => d.uri.toString() === uri.toString());
            if (targetDoc) {
                lintDocument(targetDoc);
            }
        }
    });
}

function getPythonPath() {
    const config = vscode.workspace.getConfiguration('sv-nd-scribe');
    const configured = config.get('pythonPath');
    if (configured && configured !== 'python3' && configured !== 'python') {
        return configured;
    }
    if (process.platform === 'win32') {
        return (configured === 'python3') ? 'python' : (configured || 'python');
    }
    return configured || 'python3';
}

function getExecutionEnv(scribeHome) {
    const config = vscode.workspace.getConfiguration('sv-nd-scribe');
    const projectConfig = config.get('projectConfig');
    const userEnv = config.get('env') || {};
    const env = Object.assign({}, process.env, userEnv);

    if (scribeHome) {
        env.SVND_SCRIBE_HOME = scribeHome;
        const currentPyPath = env.PYTHONPATH || '';
        const pathSep = process.platform === 'win32' ? ';' : ':';
        env.PYTHONPATH = currentPyPath ? `${scribeHome}${pathSep}${currentPyPath}` : scribeHome;
    }

    if (projectConfig) {
        env.SV_ND_SCRIBE_PROJECT_CONFIG = projectConfig;
    }

    return env;
}

function getScribeHome(documentUri) {
    const config = vscode.workspace.getConfiguration('sv-nd-scribe');
    const configuredHome = config.get('scribeHome');
    if (configuredHome) return configuredHome;
    if (process.env.SVND_SCRIBE_HOME) return process.env.SVND_SCRIBE_HOME;

    // Check starting from document directory upwards
    if (documentUri && documentUri.fsPath) {
        let curr = path.dirname(documentUri.fsPath);
        for (let i = 0; i < 10; i++) {
            if (fs.existsSync(path.join(curr, 'agent')) && fs.existsSync(path.join(curr, 'linter'))) {
                return curr;
            }
            const parent = path.dirname(curr);
            if (parent === curr) break;
            curr = parent;
        }
    }

    // Check workspace folders
    if (vscode.workspace.workspaceFolders) {
        for (const wf of vscode.workspace.workspaceFolders) {
            const root = wf.uri.fsPath;
            if (fs.existsSync(path.join(root, 'agent')) && fs.existsSync(path.join(root, 'linter'))) {
                return root;
            }
        }
    }

    // Check extension folder parents
    let curr = __dirname;
    for (let i = 0; i < 5; i++) {
        if (fs.existsSync(path.join(curr, 'agent')) && fs.existsSync(path.join(curr, 'linter'))) {
            return curr;
        }
        const parent = path.dirname(curr);
        if (parent === curr) break;
        curr = parent;
    }

    return null;
}

function getLinterPath(scribeHome) {
    const home = scribeHome || getScribeHome();
    if (home) {
        const candidate = path.join(home, 'linter', '__main__.py');
        if (fs.existsSync(candidate)) {
            return candidate;
        }
    }
    return null;
}

function deactivate() {
    if (diagnosticCollection) {
        diagnosticCollection.clear();
        diagnosticCollection.dispose();
    }
    if (statusDiagnosticCollection) {
        statusDiagnosticCollection.clear();
        statusDiagnosticCollection.dispose();
    }
}

module.exports = {
    activate,
    deactivate
};
