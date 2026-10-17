try { const t=localStorage.getItem('brief-theme'); if(t==='dark'||t==='light') document.documentElement.dataset.theme=t; } catch {}
