const nav=document.querySelector('.nav'),btn=document.querySelector('.menu');
btn&&btn.addEventListener('click',()=>{const o=nav.classList.toggle('open');btn.setAttribute('aria-expanded',o)});
document.querySelectorAll('.nav a').forEach(a=>a.addEventListener('click',()=>nav.classList.remove('open')));
document.querySelectorAll('[data-pick]').forEach(b=>b.addEventListener('click',()=>{
  const s=document.querySelector('#id_cylinder'); if(s) s.value=b.dataset.pick;}));
