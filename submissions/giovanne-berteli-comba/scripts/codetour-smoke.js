// Run with VS Code --extensionTestsPath in an isolated extension host; never by the app launcher.
const vscode = require('vscode');
const fs = require('fs');
const path = require('path');
const assert = require('assert');
const waitFor = async predicate => { for(let i=0;i<100;i++){if(predicate())return;await new Promise(r=>setTimeout(r,50));}throw new Error('Editor did not navigate to the expected anchor');};
exports.run = async function(){
 const extension = vscode.extensions.getExtension('vsls-contrib.codetour');
 assert(extension,'Installed CodeTour not found in isolated extension host');
 const api = await extension.activate();
 let started = null;
 const subscription=api.onDidStartTour(value=>{started=value;});
 await vscode.commands.executeCommand('codetour.startTourByTitle','Triagem IT assistida — revisão guiada');
 await new Promise(r=>setTimeout(r,500));
 const expected=process.env.TRIAGE_TOUR_EXPECT==='true';
 assert.strictEqual(Boolean(started),expected,'Actual extension discovery differs from expected workspace behavior');
 const result={extension:extension.id,version:extension.packageJSON.version,discovered:Boolean(started),anchors:[]};
 if(expected){
  const tour=started[0];
  const root=vscode.workspace.workspaceFolders[0].uri.fsPath;
  for(let i=0;i<tour.steps.length;i++){
   const step=tour.steps[i];
   const text=fs.readFileSync(path.join(root,step.file),'utf8');
   const matches=text.split(/\r?\n/).map((line,index)=>({line,index})).filter(item=>new RegExp(step.pattern).test(item.line));
   assert.strictEqual(matches.length,1,`JS pattern failed for ${step.file}`);
   await vscode.commands.executeCommand('codetour.navigateToStep',i+1);
   await waitFor(()=>vscode.window.activeTextEditor && path.resolve(vscode.window.activeTextEditor.document.uri.fsPath)===path.resolve(root,step.file) && vscode.window.activeTextEditor.selection.active.line===matches[0].index);
   result.anchors.push({file:step.file,line:matches[0].index+1});
  }
  await api.endCurrentTour();
 }
 subscription.dispose();
 fs.writeFileSync(process.env.TRIAGE_TOUR_RESULT,JSON.stringify(result,null,2));
};
