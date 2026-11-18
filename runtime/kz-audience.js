/* Audience policy: automatic motion, no playback UI. Does not own navigation. */
(function(){'use strict';
 const selector='.kz-film-controls,[data-kz-pause],[data-kz-replay],input[data-kz-progress],[data-kz-progress-text],[data-kz-motion-toggle],.kz-motion-toggle,.kz-motion-ctl,#motion-toggle,#kz-motion-toggle,#replay-chart';
 const playerText=/^(?:暂停(?:动效|动画|播放)?|继续(?:动效|动画|播放)|动效|播放(?:动画|动效)?|开始动画|停止动画|重新播放|重播|重放|恢复播放|开始播放下一页|播放下一页|停止所有动画|Play|Pause|Replay|Resume animation)$/i;
 function clean(root){
  const targets=[];
  if(root.nodeType===1&&root.matches(selector))targets.push(root);
  if(root.querySelectorAll)targets.push(...root.querySelectorAll(selector));
  for(const e of targets)e.remove();
  const buttons=root.querySelectorAll?[...root.querySelectorAll('button,[role="button"]')]:[];
  if(root.nodeType===1&&root.matches('button,[role="button"]'))buttons.push(root);
  for(const b of buttons)if(playerText.test(b.textContent.trim()))b.remove();
 }
 function start(){clean(document);const observer=new MutationObserver(records=>{for(const r of records)for(const n of r.addedNodes)if(n.nodeType===1)clean(n);});observer.observe(document.body,{childList:true,subtree:true});}
 if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',start,{once:true});else start();
})();
