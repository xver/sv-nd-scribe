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
                    const cleanOut = (stdout || "").split("\n").filter(l => !l.startsWith("sv-nd-scribe: Warning:")).join("\n").trim();
                    vscode.window.showInformationMessage(`SV ND Scribe Status: ${cleanOut || "OK"}`);
                }
            }
            if (diagnostics.length > 0) {
                diagnostics.forEach(d => d.source = 'sv-nd-scribe-status');
                statusDiagnosticCollection.set(getErrorUri(), diagnostics);
            }
        });
    };

    context.subscriptions.push(vscode.commands.registerCommand('sv-nd-scribe.status', () => statusHandler(false)));
    context.subscriptions.push(vscode.commands.registerCommand('sv-nd-scribe.verifyInstallation', () => verifyInstallationHandler()));

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

/**
 * Resolve VS Code variable references like ${workspaceFolder} in a string.
 * VS Code does NOT substitute these when settings are read via getConfiguration(),
 * so we must do it ourselves before passing values to child processes.
 */
function resolveVscodeVariables(value) {
    if (typeof value !== 'string') return value;
    const wsFolders = vscode.workspace.workspaceFolders;
    if (wsFolders && wsFolders.length > 0) {
        const hadVariable = value.includes('${workspaceFolder}');
        value = value.replace(/\$\{workspaceFolder\}/g, wsFolders[0].uri.fsPath);
        // Normalize path separators to avoid mixed slashes (e.g. UNC backslashes + forward slashes)
        if (hadVariable) {
            if (!value.startsWith("\\\\wsl") && !value.startsWith("//wsl")) {
                value = path.normalize(value);
            }
        }
    }
    return value;
}

function getExecutionEnv(scribeHome) {
    const config = vscode.workspace.getConfiguration('sv-nd-scribe');
    const projectConfig = config.get('projectConfig');
    const userEnv = config.get('env') || {};

    // Resolve ${workspaceFolder} in all user-supplied env values
    const resolvedUserEnv = {};
    for (const [key, val] of Object.entries(userEnv)) {
        resolvedUserEnv[key] = resolveVscodeVariables(val);
    }
    const env = Object.assign({}, process.env, resolvedUserEnv);

    if (scribeHome) {
        env.SVND_SCRIBE_HOME = scribeHome;
        const currentPyPath = env.PYTHONPATH || '';
        const pathSep = process.platform === 'win32' ? ';' : ':';
        env.PYTHONPATH = currentPyPath ? `${scribeHome}${pathSep}${currentPyPath}` : scribeHome;
    }

    if (projectConfig) {
        env.SV_ND_SCRIBE_PROJECT_CONFIG = resolveVscodeVariables(projectConfig);
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


// ─────────────────────────────────────────────────────────────────────────────
// Interactive Verify Installation — Step-by-Step Prerequisite Checker
// Checks all Quick-Start Guide prerequisites (Steps 1–7) using only Node.js
// APIs and child_process, so it works even when the repository is not yet
// downloaded.  Each step is reported to the user via a progress notification
// with actionable fix buttons on failure.
// ─────────────────────────────────────────────────────────────────────────────

/**
 * Spawn a command and return { stdout, stderr, code }.
 * Resolves (never rejects) so callers can inspect the exit code.
 */
function spawnCheck(command, args, options) {
    return new Promise((resolve) => {
        child_process.execFile(command, args, options || {}, (error, stdout, stderr) => {
            resolve({
                stdout: (stdout || '').trim(),
                stderr: (stderr || '').trim(),
                code: error ? (error.code || 1) : 0,
                error: error || null,
            });
        });
    });
}

async function verifyInstallationHandler() {
    const TOTAL_STEPS = 7;
    const GITHUB_REPO = 'https://github.com/xver/sv-nd-scribe';

    await vscode.window.withProgress(
        {
            location: vscode.ProgressLocation.Notification,
            title: 'SV ND Scribe — Verifying Installation',
            cancellable: false,
        },
        async (progress) => {
            const results = [];
            let stopEarly = false;

            const report = (step, name, status, detail) => {
                const icon = status === 'pass' ? '✅' : status === 'warn' ? '⚠️' : '❌';
                const msg = `${icon} Step ${step}/${TOTAL_STEPS}: ${name} — ${detail}`;
                results.push({ step, name, status, detail });
                if (outputChannel) outputChannel.appendLine(msg);
                progress.report({ message: `Step ${step}/${TOTAL_STEPS}: ${name}...`, increment: Math.round(100 / TOTAL_STEPS) });
            };

            // ── Step 1: Python ──────────────────────────────────────────
            progress.report({ message: 'Step 1/7: Checking Python...', increment: 0 });
            let pythonCmd = getPythonPath();
            let pythonVersion = null;
            {
                const res = await spawnCheck(pythonCmd, ['--version']);
                if (res.error && (res.error.code === 'ENOENT' || res.error.errno === -4058)) {
                    // Try fallback
                    const alt = pythonCmd === 'python3' ? 'python' : 'python3';
                    const res2 = await spawnCheck(alt, ['--version']);
                    if (res2.error && (res2.error.code === 'ENOENT' || res2.error.errno === -4058)) {
                        report(1, 'Python 3', 'fail', 'Python interpreter not found');
                        const action = await vscode.window.showErrorMessage(
                            'SV ND Scribe: Step 1 — Python 3.9+ is not installed or not in PATH.',
                            'Install Python'
                        );
                        if (action === 'Install Python') {
                            vscode.env.openExternal(vscode.Uri.parse('https://www.python.org/downloads/'));
                        }
                        stopEarly = true;
                    } else {
                        pythonCmd = alt;
                        pythonVersion = (res2.stdout || res2.stderr).replace(/^Python\s*/i, '');
                    }
                } else if (res.code === 0 || res.stdout) {
                    pythonVersion = (res.stdout || res.stderr).replace(/^Python\s*/i, '');
                } else {
                    report(1, 'Python 3', 'fail', `Python returned error: ${res.stderr || res.stdout}`);
                    const action = await vscode.window.showErrorMessage(
                        `SV ND Scribe: Step 1 — Python error: ${res.stderr || res.stdout}`,
                        'Install Python'
                    );
                    if (action === 'Install Python') {
                        vscode.env.openExternal(vscode.Uri.parse('https://www.python.org/downloads/'));
                    }
                    stopEarly = true;
                }

                if (!stopEarly && pythonVersion) {
                    const parts = pythonVersion.split('.').map(Number);
                    if (parts[0] < 3 || (parts[0] === 3 && parts[1] < 9)) {
                        report(1, 'Python 3', 'fail', `Python ${pythonVersion} found — 3.9+ required`);
                        const action = await vscode.window.showErrorMessage(
                            `SV ND Scribe: Step 1 — Python ${pythonVersion} is too old. Version 3.9 or newer is required.`,
                            'Install Python'
                        );
                        if (action === 'Install Python') {
                            vscode.env.openExternal(vscode.Uri.parse('https://www.python.org/downloads/'));
                        }
                        stopEarly = true;
                    } else {
                        report(1, 'Python 3', 'pass', `Python ${pythonVersion}`);
                    }
                }
            }
            if (stopEarly) { showSummary(results, TOTAL_STEPS); return; }

            // ── Step 2: Verible ─────────────────────────────────────────
            progress.report({ message: 'Step 2/7: Checking Verible...' });
            {
                let found = false;
                for (const bin of ['verible-verilog-syntax', 'verible-verilog-syntax.exe']) {
                    const res = await spawnCheck(bin, ['--version']);
                    if (!(res.error && (res.error.code === 'ENOENT' || res.error.errno === -4058))) {
                        const ver = (res.stdout || res.stderr || '').split('\n')[0];
                        report(2, 'Verible', 'pass', `${bin} ${ver}`);
                        found = true;
                        break;
                    }
                }
                if (!found) {
                    // Check VERIBLE_HOME
                    const veribleHome = process.env.VERIBLE_HOME;
                    if (veribleHome) {
                        for (const bin of ['verible-verilog-syntax', 'verible-verilog-syntax.exe']) {
                            const fullPath = path.join(veribleHome, 'bin', bin);
                            const fullPath2 = path.join(veribleHome, bin);
                            if (fs.existsSync(fullPath) || fs.existsSync(fullPath2)) {
                                report(2, 'Verible', 'pass', `Found via VERIBLE_HOME: ${veribleHome}`);
                                found = true;
                                break;
                            }
                        }
                    }
                }
                if (!found) {
                    report(2, 'Verible', 'fail', 'verible-verilog-syntax not found in PATH or VERIBLE_HOME');
                    const action = await vscode.window.showErrorMessage(
                        'SV ND Scribe: Step 2 — verible-verilog-syntax is not installed. Download it from the Verible releases page.',
                        'Download Verible'
                    );
                    if (action === 'Download Verible') {
                        vscode.env.openExternal(vscode.Uri.parse('https://github.com/chipsalliance/verible/releases'));
                    }
                    stopEarly = true;
                }
            }
            if (stopEarly) { showSummary(results, TOTAL_STEPS); return; }

            // ── Step 3: PyYAML ──────────────────────────────────────────
            progress.report({ message: 'Step 3/7: Checking PyYAML...' });
            {
                const res = await spawnCheck(pythonCmd, ['-c', 'import yaml; print(yaml.__version__)']);
                if (res.code !== 0) {
                    report(3, 'PyYAML', 'fail', 'Python package "pyyaml" is not installed');
                    const action = await vscode.window.showErrorMessage(
                        'SV ND Scribe: Step 3 — PyYAML is not installed. Run: pip install pyyaml',
                        'Copy Command'
                    );
                    if (action === 'Copy Command') {
                        await vscode.env.clipboard.writeText('pip install pyyaml');
                        vscode.window.showInformationMessage('Copied "pip install pyyaml" to clipboard.');
                    }
                    stopEarly = true;
                } else {
                    report(3, 'PyYAML', 'pass', `PyYAML ${res.stdout}`);
                }
            }
            if (stopEarly) { showSummary(results, TOTAL_STEPS); return; }

            // ── Step 4: Repository downloaded ───────────────────────────
            progress.report({ message: 'Step 4/7: Checking sv-nd-scribe repository...' });
            let repoPath = null;
            {
                // Try multiple ways to find the repository
                const scribeHome = getScribeHome();
                if (scribeHome && fs.existsSync(path.join(scribeHome, 'linter')) && fs.existsSync(path.join(scribeHome, 'agent'))) {
                    repoPath = scribeHome;
                    report(4, 'Repository', 'pass', `Found at ${repoPath}`);
                } else {
                    report(4, 'Repository', 'fail', 'sv-nd-scribe repository not found on this machine');
                    const action = await vscode.window.showErrorMessage(
                        'SV ND Scribe: Step 4 — The sv-nd-scribe repository is not downloaded yet. Clone it from GitHub.',
                        'Open GitHub', 'Copy Clone Command'
                    );
                    if (action === 'Open GitHub') {
                        vscode.env.openExternal(vscode.Uri.parse(GITHUB_REPO));
                    } else if (action === 'Copy Clone Command') {
                        await vscode.env.clipboard.writeText(`git clone ${GITHUB_REPO}.git`);
                        vscode.window.showInformationMessage(`Copied "git clone ${GITHUB_REPO}.git" to clipboard.`);
                    }
                    stopEarly = true;
                }
            }
            if (stopEarly) { showSummary(results, TOTAL_STEPS); return; }

            // ── Step 5: SVND_SCRIBE_HOME ────────────────────────────────
            progress.report({ message: 'Step 5/7: Checking SVND_SCRIBE_HOME...' });
            {
                const config = vscode.workspace.getConfiguration('sv-nd-scribe');
                const envSetting = config.get('env') || {};
                const envHome = envSetting.SVND_SCRIBE_HOME;
                const processHome = process.env.SVND_SCRIBE_HOME;
                const configuredHome = config.get('scribeHome');

                // Detect user-level settings overriding workspace-level settings
                const envInspection = config.inspect('env');
                const userLevelEnv = envInspection ? envInspection.globalValue : undefined;
                const workspaceLevelEnv = envInspection ? envInspection.workspaceValue : undefined;
                const userOverridesWorkspace = userLevelEnv !== undefined
                    && workspaceLevelEnv !== undefined
                    && workspaceLevelEnv.SVND_SCRIBE_HOME
                    && (!userLevelEnv.SVND_SCRIBE_HOME);

                if (configuredHome || processHome || envHome) {
                    const resolved = configuredHome || processHome || envHome;
                    report(5, 'SVND_SCRIBE_HOME', 'pass', `Set to "${resolved}"`);
                } else if (repoPath) {
                    // Build the env object to write
                    const fixEnv = {
                        SVND_SCRIBE_HOME: '${workspaceFolder}',
                        PYTHONPATH: '${workspaceFolder}',
                        SV_ND_SCRIBE_PROJECT_CONFIG: '${workspaceFolder}/linter/configs'
                    };

                    if (userOverridesWorkspace) {
                        // User-level empty/incomplete env is overriding workspace-level config
                        report(5, 'SVND_SCRIBE_HOME', 'warn',
                            `Not explicitly set. User-level settings override workspace-level configuration. ` +
                            `Repository auto-detected at "${repoPath}".`);
                        const action = await vscode.window.showWarningMessage(
                            'SV ND Scribe: Step 5 — User-level "sv-nd-scribe.env" is overriding workspace settings. ' +
                            'Click "Fix Now" to update your user settings automatically.',
                            'Fix Now', 'Open Settings'
                        );
                        if (action === 'Fix Now') {
                            await config.update('env', fixEnv, vscode.ConfigurationTarget.Global);
                            vscode.window.showInformationMessage(
                                'SV ND Scribe: SVND_SCRIBE_HOME configured in user settings. Please reload the window for changes to take effect.',
                                'Reload Window'
                            ).then(reload => {
                                if (reload === 'Reload Window') {
                                    vscode.commands.executeCommand('workbench.action.reloadWindow');
                                }
                            });
                        } else if (action === 'Open Settings') {
                            vscode.commands.executeCommand('workbench.action.openSettings', 'sv-nd-scribe.env');
                        }
                    } else {
                        // No user-level override — just not set anywhere
                        report(5, 'SVND_SCRIBE_HOME', 'warn',
                            `Not explicitly set, but repository auto-detected at "${repoPath}". ` +
                            'Consider setting SVND_SCRIBE_HOME for reliability.');
                        const action = await vscode.window.showWarningMessage(
                            'SV ND Scribe: Step 5 — SVND_SCRIBE_HOME is not explicitly set. ' +
                            'Click "Fix Now" to configure it automatically, or open settings to do it manually.',
                            'Fix Now', 'Open Settings', 'Copy Setup Command'
                        );
                        if (action === 'Fix Now') {
                            // Write to workspace level if a workspace is open, otherwise user level
                            const target = vscode.workspace.workspaceFolders
                                ? vscode.ConfigurationTarget.Workspace
                                : vscode.ConfigurationTarget.Global;
                            await config.update('env', fixEnv, target);
                            const targetName = target === vscode.ConfigurationTarget.Workspace ? 'workspace' : 'user';
                            vscode.window.showInformationMessage(
                                `SV ND Scribe: SVND_SCRIBE_HOME configured in ${targetName} settings. Please reload the window for changes to take effect.`,
                                'Reload Window'
                            ).then(reload => {
                                if (reload === 'Reload Window') {
                                    vscode.commands.executeCommand('workbench.action.reloadWindow');
                                }
                            });
                        } else if (action === 'Open Settings') {
                            vscode.commands.executeCommand('workbench.action.openSettings', 'sv-nd-scribe.env');
                        } else if (action === 'Copy Setup Command') {
                            const setupCmd = `python3 ${path.join(repoPath, 'makedir', 'setup_workspace.py')}`;
                            await vscode.env.clipboard.writeText(setupCmd);
                            vscode.window.showInformationMessage(`Copied "${setupCmd}" to clipboard.`);
                        }
                    }
                    // Continue — this is a warning, not a hard failure
                } else {
                    report(5, 'SVND_SCRIBE_HOME', 'fail', 'SVND_SCRIBE_HOME is not set and repository could not be auto-detected');
                    const action = await vscode.window.showErrorMessage(
                        'SV ND Scribe: Step 5 — SVND_SCRIBE_HOME environment variable is not set and the repository could not be auto-detected. ' +
                        'Set it to the root of the sv-nd-scribe repository.',
                        'Open Settings'
                    );
                    if (action === 'Open Settings') {
                        vscode.commands.executeCommand('workbench.action.openSettings', 'sv-nd-scribe.env');
                    }
                    stopEarly = true;
                }
            }
            if (stopEarly) { showSummary(results, TOTAL_STEPS); return; }

            // ── Step 6: Workspace configuration ─────────────────────────
            progress.report({ message: 'Step 6/7: Checking workspace configuration...' });
            {
                let settingsFound = false;
                let envFileFound = false;
                let configDirFound = false;

                if (vscode.workspace.workspaceFolders && vscode.workspace.workspaceFolders.length > 0) {
                    const wsRoot = vscode.workspace.workspaceFolders[0].uri.fsPath;
                    const settingsPath = path.join(wsRoot, '.vscode', 'settings.json');
                    const envPath = path.join(wsRoot, '.env');
                    const configFilePath = path.join(wsRoot, 'linter', 'configs', 'lint_config.json');

                    if (fs.existsSync(settingsPath)) {
                        try {
                            const raw = fs.readFileSync(settingsPath, 'utf-8');
                            if (raw.includes('sv-nd-scribe')) {
                                settingsFound = true;
                            }
                        } catch (e) {
                            // ignore read errors
                        }
                    }
                    envFileFound = fs.existsSync(envPath);
                    configDirFound = fs.existsSync(configFilePath);
                } else if (repoPath) {
                    const configFilePath = path.join(repoPath, 'linter', 'configs', 'lint_config.json');
                    configDirFound = fs.existsSync(configFilePath);
                }

                if (settingsFound && envFileFound && configDirFound) {
                    report(6, 'Workspace config', 'pass', '.vscode/settings.json, .env, and lint_config.json are configured');
                } else {
                    const missing = [];
                    if (!settingsFound) missing.push('.vscode/settings.json');
                    if (!envFileFound) missing.push('.env');
                    if (!configDirFound) missing.push('linter/configs/lint_config.json');
                    const missingMsg = missing.join(', ');

                    report(6, 'Workspace config', 'warn', `Partially configured — missing ${missingMsg}`);
                    const action = await vscode.window.showWarningMessage(
                        `SV ND Scribe: Step 6 — Workspace requires configuration (missing ${missingMsg}). Click "Auto-Fix with Agent" to configure automatically.`,
                        'Auto-Fix with Agent', 'Copy Setup Command'
                    );
                    if (action === 'Auto-Fix with Agent' && repoPath) {
                        const fixRes = await spawnCheck(pythonCmd, ['-m', 'agent', '--fix-setup'], { cwd: repoPath });
                        if (fixRes.code === 0) {
                            vscode.window.showInformationMessage(
                                'SV ND Scribe: Workspace auto-repaired successfully! Please reload window for changes to take effect.',
                                'Reload Window'
                            ).then(reload => {
                                if (reload === 'Reload Window') {
                                    vscode.commands.executeCommand('workbench.action.reloadWindow');
                                }
                            });
                        } else {
                            vscode.window.showWarningMessage(`SV ND Scribe: Auto-repair completed with warning: ${fixRes.stderr || fixRes.stdout}`);
                        }
                    } else if (action === 'Copy Setup Command' && repoPath) {
                        const setupCmd = `python3 ${path.join(repoPath, 'makedir', 'setup_workspace.py')}`;
                        await vscode.env.clipboard.writeText(setupCmd);
                        vscode.window.showInformationMessage(`Copied "${setupCmd}" to clipboard.`);
                    }
                    // Continue — warning only
                }
            }

            // ── Step 7: Linter module loads ─────────────────────────────
            progress.report({ message: 'Step 7/7: Checking linter module...' });
            {
                const env = getExecutionEnv(repoPath);
                const execOptions = { env };
                if (repoPath) execOptions.cwd = repoPath;

                const linterPath = getLinterPath(repoPath);
                if (!linterPath) {
                    report(7, 'Linter module', 'fail', 'linter/__main__.py not found in repository');
                    vscode.window.showErrorMessage(
                        'SV ND Scribe: Step 7 — Linter module not found. The repository may be incomplete or corrupted. Try re-downloading.'
                    );
                } else {
                    const res = await spawnCheck(pythonCmd, [linterPath, '--status'], execOptions);
                    if (res.code !== 0) {
                        const errMsg = res.stdout || res.stderr || 'Unknown error';
                        report(7, 'Linter module', 'fail', errMsg);
                        vscode.window.showErrorMessage(
                            `SV ND Scribe: Step 7 — Linter failed to initialize: ${errMsg}`
                        );
                    } else {
                        report(7, 'Linter module', 'pass', res.stdout || 'Linter loaded successfully');
                    }
                }
            }

            showSummary(results, TOTAL_STEPS);
        }
    );
}

function showSummary(results, totalSteps) {
    if (!outputChannel) return;

    outputChannel.appendLine('');
    outputChannel.appendLine('═══════════════════════════════════════════════════════');
    outputChannel.appendLine('  SV ND Scribe — Installation Verification Summary');
    outputChannel.appendLine('═══════════════════════════════════════════════════════');

    const passed = results.filter(r => r.status === 'pass').length;
    const warned = results.filter(r => r.status === 'warn').length;
    const failed = results.filter(r => r.status === 'fail').length;
    const skipped = totalSteps - results.length;

    for (const r of results) {
        const icon = r.status === 'pass' ? '✅' : r.status === 'warn' ? '⚠️' : '❌';
        outputChannel.appendLine(`  ${icon} Step ${r.step}: ${r.name} — ${r.detail}`);
    }
    if (skipped > 0) {
        outputChannel.appendLine(`  ⏭️  ${skipped} step(s) skipped (fix earlier failures first)`);
    }

    outputChannel.appendLine('');
    outputChannel.appendLine(`  Result: ${passed} passed, ${warned} warnings, ${failed} failed, ${skipped} skipped`);
    outputChannel.appendLine('═══════════════════════════════════════════════════════');
    outputChannel.appendLine('');
    outputChannel.show(true);

    if (failed === 0 && skipped === 0) {
        if (warned === 0) {
            vscode.window.showInformationMessage('✅ SV ND Scribe: All 7 checks passed. Installation is ready!');
        } else {
            vscode.window.showInformationMessage(`✅ SV ND Scribe: All checks passed (${warned} warning${warned > 1 ? 's' : ''}). See Output for details.`);
        }
    } else if (failed > 0) {
        vscode.window.showErrorMessage(`❌ SV ND Scribe: ${failed} check(s) failed. Fix the issue above, then re-run "Verify linter installation". See Output panel for details.`);
    }
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
