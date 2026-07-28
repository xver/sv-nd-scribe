/**
 * SV ND Scribe - VS Code Extension
 * Provides real-time in-editor diagnostics for SystemVerilog files.
 */
const vscode = require('vscode');
const child_process = require('child_process');

let diagnosticCollection;

function activate(context) {
    diagnosticCollection = vscode.languages.createDiagnosticCollection('sv-nd-scribe');
    context.subscriptions.push(diagnosticCollection);

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
        })
    );
}

function lintDocument(document) {
    if (document.languageId !== 'systemverilog' && document.languageId !== 'verilog') {
        return;
    }

    const config = vscode.workspace.getConfiguration('sv-nd-scribe');
    const pythonPath = config.get('pythonPath') || 'python3';
    const linterPath = config.get('linterPath');
    
    if (!linterPath) {
        return;
    }

    const filePath = document.uri.fsPath;
    
    // Execute linter process
    child_process.execFile(pythonPath, [linterPath, filePath], (error, stdout, stderr) => {
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
                let lineText = '';
                if (lineNum >= 0 && lineNum < document.lineCount) {
                    lineText = document.lineAt(lineNum).text;
                }
                const startChar = lineText.length - lineText.trimStart().length;
                const endChar = lineText.length;
                const range = new vscode.Range(lineNum, startChar, lineNum, endChar > 0 ? endChar : 100);

                const diagnostic = new vscode.Diagnostic(range, `${ruleId}: ${message}`, severity);
                diagnostic.code = ruleId;
                diagnostic.source = 'sv-nd-scribe';

                const targetUri = vscode.Uri.file(file);
                const targetKey = targetUri.toString();

                if (!diagnosticsMap.has(targetKey)) {
                    diagnosticsMap.set(targetKey, []);
                }
                diagnosticsMap.get(targetKey).push(diagnostic);
            }
        }

        // Reset diagnostics for this document
        diagnosticCollection.set(document.uri, []);
        
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
}

module.exports = {
    activate,
    deactivate
};
