const fs = require('fs');
for (const file of [
  '/var/home/work/gitdir/test-tina-rag/easy/.venv/lib/python3.14/site-packages/tina4_python/public/js/tina4-dev-admin.js',
  '/var/home/work/gitdir/test-tina-rag/easy/.venv/lib/python3.14/site-packages/tina4_python/public/js/tina4-dev-admin.min.js'
]) {
  let code = fs.readFileSync(file, 'utf8');
  
  // Patch Qa
  code = code.replace(
    /function Qa\(\)\{const i=e=>document\.getElementById\(e\);i\(\"threads-pane-head-list\"\)\.hidden=!1,i\(\"threads-pane-head-detail\"\)\.hidden=!0,i\(\"threads-list-view\"\)\.hidden=!1,i\(\"threads-detail-view\"\)\.hidden=!0,ld\(\)\.then\(Os\)\}/g,
    'function Qa(){const i=e=>document.getElementById(e);const a=i(\"threads-pane-head-list\");if(a)a.hidden=!1;const b=i(\"threads-pane-head-detail\");if(b)b.hidden=!0;const c=i(\"threads-list-view\");if(c)c.hidden=!1;const d=i(\"threads-detail-view\");if(d)d.hidden=!0;ld().then(Os)}'
  );

  // Patch hd
  code = code.replace(
    /async function hd\(i\)\{await Od\(i\);const e=Te\.find\(s=>s\.id===i\);if\(!e\)return;const t=s=>document\.getElementById\(s\);t\(\"threads-pane-head-list\"\)\.hidden=!0,t\(\"threads-pane-head-detail\"\)\.hidden=!1,t\(\"threads-list-view\"\)\.hidden=!0,t\(\"threads-detail-view\"\)\.hidden=!1,t\(\"threads-detail-title\"\)\.textContent=e\.title\|\|\"Thread\";const n=t\(\"threads-detail-meta\"\),r=e\.sender\?\`<span>📨 from \$\{g\(e\.sender\)\}<\/span>\`\:\"\";n\.innerHTML=\`\$\{cd\(e\.status_hint\|\|\"idle\"\)\} <span>\$\{g\(dd\(e\.last_message_at\)\)\}<\/span> \$\{r\}\`,ud\(i\),setTimeout\(\(\)=>\{var s;return\(s=t\(\"threads-reply-input\"\)\)==null\?void 0\:s\.focus\(\)\},30\)\}/g,
    'async function hd(i){await Od(i);const e=Te.find(s=>s.id===i);if(!e)return;const t=s=>document.getElementById(s);const h1=t(\"threads-pane-head-list\");if(h1)h1.hidden=!0;const h2=t(\"threads-pane-head-detail\");if(h2)h2.hidden=!1;const v1=t(\"threads-list-view\");if(v1)v1.hidden=!0;const v2=t(\"threads-detail-view\");if(v2)v2.hidden=!1;const dt=t(\"threads-detail-title\");if(dt)dt.textContent=e.title||\"Thread\";const n=t(\"threads-detail-meta\"),r=e.sender?`<span>📨 from ${g(e.sender)}</span>`:\"\";if(n)n.innerHTML=`${cd(e.status_hint||\"idle\")} <span>${g(dd(e.last_message_at))}</span> ${r}`;ud(i);setTimeout(()=>{var s;return(s=t(\"threads-reply-input\"))==null?void 0:s.focus()},30)}'
  );
  
  fs.writeFileSync(file, code);
  console.log('Patched ' + file);
}
