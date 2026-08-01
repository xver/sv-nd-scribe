/**
 * SV ND Scribe - VS Code Extension
 * Provides real-time in-editor diagnostics for SystemVerilog files.
 */
const vscode = require('vscode');
const child_process = require('child_process');

let diagnosticCollection;
let statusDiagnosticCollection;

function activate(context) {
    diagnosticCollection = vscode.languages.createDiagnosticCollection('sv-nd-scribe');
    context.subscriptions.push(diagnosticCollection);
    statusDiagnosticCollection = vscode.languages.createDiagnosticCollection('sv-nd-scribe-status');
    context.subscriptions.push(statusDiagnosticCollection);

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
        const configuredLinterPath = config.get('linterPath');
        const pythonPath = config.get('pythonPath') || 'python3';
        const linterPath = getLinterPath();

        if (!process.env.SVND_SCRIBE_HOME) {
            if (configuredLinterPath) {
                const msg = `SV ND Scribe Status: Warning: SVND_SCRIBE_HOME is not set. Using configured path: ${configuredLinterPath}`;
                if (!isStartup) {
                    vscode.window.showWarningMessage(msg);
                }
                diagnostics.push(new vscode.Diagnostic(
                    new vscode.Range(0, 0, 0, 100),
                    msg,
                    vscode.DiagnosticSeverity.Warning
                ));
            } else {
                const msg = 'SV ND Scribe Status: Error: SVND_SCRIBE_HOME environment variable is missing.';
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

        const env = { ...process.env };
        if (!env.SVND_SCRIBE_HOME && linterPath) {
            const path = require('path');
            env.SVND_SCRIBE_HOME = path.dirname(path.dirname(linterPath));
        }

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
    
    // Execute linter process
    child_process.execFile(pythonPath, [linterPath, ...filePaths], (error, stdout, stderr) => {
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

function deactivate() {
    if (diagnosticCollection) {
        diagnosticCollection.clear();
    }
    if (statusDiagnosticCollection) {
        statusDiagnosticCollection.clear();
    }
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

module.exports = {
    activate,
    deactivate
};
