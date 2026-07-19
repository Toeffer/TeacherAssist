import{t as e}from"./jsx-runtime-CdvZGgm7.js";var t=e(),n=`
  .twk-panel{position:fixed;right:16px;bottom:16px;z-index:2147483646;width:280px;
    max-height:calc(100vh - 32px);display:flex;flex-direction:column;
    background:rgba(250,249,247,.78);color:#29261b;
    -webkit-backdrop-filter:blur(24px) saturate(160%);backdrop-filter:blur(24px) saturate(160%);
    border:.5px solid rgba(255,255,255,.6);border-radius:14px;
    box-shadow:0 1px 0 rgba(255,255,255,.5) inset,0 12px 40px rgba(0,0,0,.18);
    font:11.5px/1.4 ui-sans-serif,system-ui,-apple-system,sans-serif;overflow:hidden}
  .twk-hd{display:flex;align-items:center;justify-content:space-between;
    padding:10px 8px 10px 14px;cursor:move;user-select:none}
  .twk-hd b{font-size:12px;font-weight:600;letter-spacing:.01em}
  .twk-x{appearance:none;border:0;background:transparent;color:rgba(41,38,27,.55);
    width:22px;height:22px;border-radius:6px;cursor:default;font-size:13px;line-height:1}
  .twk-x:hover{background:rgba(0,0,0,.06);color:#29261b}
  .twk-body{padding:2px 14px 14px;display:flex;flex-direction:column;gap:10px;
    overflow-y:auto;overflow-x:hidden;min-height:0;
    scrollbar-width:thin;scrollbar-color:rgba(0,0,0,.15) transparent}
  .twk-body::-webkit-scrollbar{width:8px}
  .twk-body::-webkit-scrollbar-track{background:transparent;margin:2px}
  .twk-body::-webkit-scrollbar-thumb{background:rgba(0,0,0,.15);border-radius:4px;
    border:2px solid transparent;background-clip:content-box}
  .twk-body::-webkit-scrollbar-thumb:hover{background:rgba(0,0,0,.25);
    border:2px solid transparent;background-clip:content-box}
  .twk-row{display:flex;flex-direction:column;gap:5px}
  .twk-row-h{flex-direction:row;align-items:center;justify-content:space-between;gap:10px}
  .twk-lbl{display:flex;justify-content:space-between;align-items:baseline;
    color:rgba(41,38,27,.72)}
  .twk-lbl>span:first-child{font-weight:500}
  .twk-val{color:rgba(41,38,27,.5);font-variant-numeric:tabular-nums}

  .twk-sect{font-size:10px;font-weight:600;letter-spacing:.06em;text-transform:uppercase;
    color:rgba(41,38,27,.45);padding:10px 0 0}
  .twk-sect:first-child{padding-top:0}

  .twk-field{appearance:none;width:100%;height:26px;padding:0 8px;
    border:.5px solid rgba(0,0,0,.1);border-radius:7px;
    background:rgba(255,255,255,.6);color:inherit;font:inherit;outline:none}
  .twk-field:focus{border-color:rgba(0,0,0,.25);background:rgba(255,255,255,.85)}
  select.twk-field{padding-right:22px;
    background-image:url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='10' height='6' viewBox='0 0 10 6'><path fill='rgba(0,0,0,.5)' d='M0 0h10L5 6z'/></svg>");
    background-repeat:no-repeat;background-position:right 8px center}

  .twk-slider{appearance:none;-webkit-appearance:none;width:100%;height:4px;margin:6px 0;
    border-radius:999px;background:rgba(0,0,0,.12);outline:none}
  .twk-slider::-webkit-slider-thumb{-webkit-appearance:none;appearance:none;
    width:14px;height:14px;border-radius:50%;background:#fff;
    border:.5px solid rgba(0,0,0,.12);box-shadow:0 1px 3px rgba(0,0,0,.2);cursor:default}
  .twk-slider::-moz-range-thumb{width:14px;height:14px;border-radius:50%;
    background:#fff;border:.5px solid rgba(0,0,0,.12);box-shadow:0 1px 3px rgba(0,0,0,.2);cursor:default}

  .twk-seg{position:relative;display:flex;padding:2px;border-radius:8px;
    background:rgba(0,0,0,.06);user-select:none}
  .twk-seg-thumb{position:absolute;top:2px;bottom:2px;border-radius:6px;
    background:rgba(255,255,255,.9);box-shadow:0 1px 2px rgba(0,0,0,.12);
    transition:left .15s cubic-bezier(.3,.7,.4,1),width .15s}
  .twk-seg.dragging .twk-seg-thumb{transition:none}
  .twk-seg button{appearance:none;position:relative;z-index:1;flex:1;border:0;
    background:transparent;color:inherit;font:inherit;font-weight:500;height:22px;
    border-radius:6px;cursor:default;padding:0}

  .twk-toggle{position:relative;width:32px;height:18px;border:0;border-radius:999px;
    background:rgba(0,0,0,.15);transition:background .15s;cursor:default;padding:0}
  .twk-toggle[data-on="1"]{background:#34c759}
  .twk-toggle i{position:absolute;top:2px;left:2px;width:14px;height:14px;border-radius:50%;
    background:#fff;box-shadow:0 1px 2px rgba(0,0,0,.25);transition:transform .15s}
  .twk-toggle[data-on="1"] i{transform:translateX(14px)}

  .twk-num{display:flex;align-items:center;height:26px;padding:0 0 0 8px;
    border:.5px solid rgba(0,0,0,.1);border-radius:7px;background:rgba(255,255,255,.6)}
  .twk-num-lbl{font-weight:500;color:rgba(41,38,27,.6);cursor:ew-resize;
    user-select:none;padding-right:8px}
  .twk-num input{flex:1;min-width:0;height:100%;border:0;background:transparent;
    font:inherit;font-variant-numeric:tabular-nums;text-align:right;padding:0 8px 0 0;
    outline:none;color:inherit;-moz-appearance:textfield}
  .twk-num input::-webkit-inner-spin-button,.twk-num input::-webkit-outer-spin-button{
    -webkit-appearance:none;margin:0}
  .twk-num-unit{padding-right:8px;color:rgba(41,38,27,.45)}

  .twk-btn{appearance:none;height:26px;padding:0 12px;border:0;border-radius:7px;
    background:rgba(0,0,0,.78);color:#fff;font:inherit;font-weight:500;cursor:default}
  .twk-btn:hover{background:rgba(0,0,0,.88)}
  .twk-btn.secondary{background:rgba(0,0,0,.06);color:inherit}
  .twk-btn.secondary:hover{background:rgba(0,0,0,.1)}

  .twk-swatch{appearance:none;-webkit-appearance:none;width:56px;height:22px;
    border:.5px solid rgba(0,0,0,.1);border-radius:6px;padding:0;cursor:default;
    background:transparent;flex-shrink:0}
  .twk-swatch::-webkit-color-swatch-wrapper{padding:0}
  .twk-swatch::-webkit-color-swatch{border:0;border-radius:5.5px}
  .twk-swatch::-moz-color-swatch{border:0;border-radius:5.5px}
`;function r(e){let[t,n]=React.useState(e);return[t,React.useCallback((e,t)=>{n(n=>({...n,[e]:t})),window.parent.postMessage({type:`__edit_mode_set_keys`,edits:{[e]:t}},`*`)},[])]}function i({title:e=`Tweaks`,children:r}){let[i,a]=React.useState(!1),o=React.useRef(null),s=React.useRef({x:16,y:16}),c=React.useCallback(()=>{let e=o.current;if(!e)return;let t=e.offsetWidth,n=e.offsetHeight,r=Math.max(16,window.innerWidth-t-16),i=Math.max(16,window.innerHeight-n-16);s.current={x:Math.min(r,Math.max(16,s.current.x)),y:Math.min(i,Math.max(16,s.current.y))},e.style.right=s.current.x+`px`,e.style.bottom=s.current.y+`px`},[]);return React.useEffect(()=>{if(!i)return;if(c(),typeof ResizeObserver>`u`)return window.addEventListener(`resize`,c),()=>window.removeEventListener(`resize`,c);let e=new ResizeObserver(c);return e.observe(document.documentElement),()=>e.disconnect()},[i,c]),React.useEffect(()=>{let e=e=>{let t=e?.data?.type;t===`__activate_edit_mode`?a(!0):t===`__deactivate_edit_mode`&&a(!1)};return window.addEventListener(`message`,e),window.parent.postMessage({type:`__edit_mode_available`},`*`),()=>window.removeEventListener(`message`,e)},[]),i?(0,t.jsxs)(t.Fragment,{children:[(0,t.jsx)(`style`,{children:n}),(0,t.jsxs)(`div`,{ref:o,className:`twk-panel`,style:{right:s.current.x,bottom:s.current.y},children:[(0,t.jsxs)(`div`,{className:`twk-hd`,onMouseDown:e=>{let t=o.current;if(!t)return;let n=t.getBoundingClientRect(),r=e.clientX,i=e.clientY,a=window.innerWidth-n.right,l=window.innerHeight-n.bottom,u=e=>{s.current={x:a-(e.clientX-r),y:l-(e.clientY-i)},c()},d=()=>{window.removeEventListener(`mousemove`,u),window.removeEventListener(`mouseup`,d)};window.addEventListener(`mousemove`,u),window.addEventListener(`mouseup`,d)},children:[(0,t.jsx)(`b`,{children:e}),(0,t.jsx)(`button`,{className:`twk-x`,"aria-label":`Close tweaks`,onMouseDown:e=>e.stopPropagation(),onClick:()=>{a(!1),window.parent.postMessage({type:`__edit_mode_dismissed`},`*`)},children:`✕`})]}),(0,t.jsx)(`div`,{className:`twk-body`,children:r})]})]}):null}function a({label:e,children:n}){return(0,t.jsxs)(t.Fragment,{children:[(0,t.jsx)(`div`,{className:`twk-sect`,children:e}),n]})}function o({label:e,value:n,children:r,inline:i=!1}){return(0,t.jsxs)(`div`,{className:i?`twk-row twk-row-h`:`twk-row`,children:[(0,t.jsxs)(`div`,{className:`twk-lbl`,children:[(0,t.jsx)(`span`,{children:e}),n!=null&&(0,t.jsx)(`span`,{className:`twk-val`,children:n})]}),r]})}function s({label:e,value:n,min:r=0,max:i=100,step:a=1,unit:s=``,onChange:c}){return(0,t.jsx)(o,{label:e,value:`${n}${s}`,children:(0,t.jsx)(`input`,{type:`range`,className:`twk-slider`,min:r,max:i,step:a,value:n,onChange:e=>c(Number(e.target.value))})})}function c({label:e,value:n,onChange:r}){return(0,t.jsxs)(`div`,{className:`twk-row twk-row-h`,children:[(0,t.jsx)(`div`,{className:`twk-lbl`,children:(0,t.jsx)(`span`,{children:e})}),(0,t.jsx)(`button`,{type:`button`,className:`twk-toggle`,"data-on":n?`1`:`0`,role:`switch`,"aria-checked":!!n,onClick:()=>r(!n),children:(0,t.jsx)(`i`,{})})]})}function l({label:e,value:n,options:r,onChange:i}){let a=React.useRef(null),[s,c]=React.useState(!1),l=r.map(e=>typeof e==`object`?e:{value:e,label:e}),u=Math.max(0,l.findIndex(e=>e.value===n)),d=l.length,f=React.useRef(n);f.current=n;let p=e=>{let t=a.current.getBoundingClientRect(),n=t.width-4,r=Math.floor((e-t.left-2)/n*d);return l[Math.max(0,Math.min(d-1,r))].value};return(0,t.jsx)(o,{label:e,children:(0,t.jsxs)(`div`,{ref:a,role:`radiogroup`,onPointerDown:e=>{c(!0);let t=p(e.clientX);t!==f.current&&i(t);let n=e=>{if(!a.current)return;let t=p(e.clientX);t!==f.current&&i(t)},r=()=>{c(!1),window.removeEventListener(`pointermove`,n),window.removeEventListener(`pointerup`,r)};window.addEventListener(`pointermove`,n),window.addEventListener(`pointerup`,r)},className:s?`twk-seg dragging`:`twk-seg`,children:[(0,t.jsx)(`div`,{className:`twk-seg-thumb`,style:{left:`calc(2px + ${u} * (100% - 4px) / ${d})`,width:`calc((100% - 4px) / ${d})`}}),l.map(e=>(0,t.jsx)(`button`,{type:`button`,role:`radio`,"aria-checked":e.value===n,children:e.label},e.value))]})})}function u({label:e,value:n,options:r,onChange:i}){return(0,t.jsx)(o,{label:e,children:(0,t.jsx)(`select`,{className:`twk-field`,value:n,onChange:e=>i(e.target.value),children:r.map(e=>{let n=typeof e==`object`?e.value:e;return(0,t.jsx)(`option`,{value:n,children:typeof e==`object`?e.label:e},n)})})})}function d({label:e,value:n,placeholder:r,onChange:i}){return(0,t.jsx)(o,{label:e,children:(0,t.jsx)(`input`,{className:`twk-field`,type:`text`,value:n,placeholder:r,onChange:e=>i(e.target.value)})})}function f({label:e,value:n,min:r,max:i,step:a=1,unit:o=``,onChange:s}){let c=e=>r!=null&&e<r?r:i!=null&&e>i?i:e,l=React.useRef({x:0,val:0});return(0,t.jsxs)(`div`,{className:`twk-num`,children:[(0,t.jsx)(`span`,{className:`twk-num-lbl`,onPointerDown:e=>{e.preventDefault(),l.current={x:e.clientX,val:n};let t=(String(a).split(`.`)[1]||``).length,r=e=>{let n=e.clientX-l.current.x,r=l.current.val+n*a,i=Math.round(r/a)*a;s(c(Number(i.toFixed(t))))},i=()=>{window.removeEventListener(`pointermove`,r),window.removeEventListener(`pointerup`,i)};window.addEventListener(`pointermove`,r),window.addEventListener(`pointerup`,i)},children:e}),(0,t.jsx)(`input`,{type:`number`,value:n,min:r,max:i,step:a,onChange:e=>s(c(Number(e.target.value)))}),o&&(0,t.jsx)(`span`,{className:`twk-num-unit`,children:o})]})}function p({label:e,value:n,onChange:r}){return(0,t.jsxs)(`div`,{className:`twk-row twk-row-h`,children:[(0,t.jsx)(`div`,{className:`twk-lbl`,children:(0,t.jsx)(`span`,{children:e})}),(0,t.jsx)(`input`,{type:`color`,className:`twk-swatch`,value:n,onChange:e=>r(e.target.value)})]})}function m({label:e,onClick:n,secondary:r=!1}){return(0,t.jsx)(`button`,{type:`button`,className:r?`twk-btn secondary`:`twk-btn`,onClick:n,children:e})}Object.assign(window,{useTweaks:r,TweaksPanel:i,TweakSection:a,TweakRow:o,TweakSlider:s,TweakToggle:c,TweakRadio:l,TweakSelect:u,TweakText:d,TweakNumber:f,TweakColor:p,TweakButton:m});