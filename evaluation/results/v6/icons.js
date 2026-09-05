// Selected Lucide 1.8.0 icons. ISC license: LUCIDE-LICENSE.txt.
const resultIcons = {"ChevronRight":[["path",{"d":"m9 18 6-6-6-6"}]],"ChevronDown":[["path",{"d":"m6 9 6 6 6-6"}]],"ArrowDown":[["path",{"d":"M12 5v14"}],["path",{"d":"m19 12-7 7-7-7"}]],"ArrowUpRight":[["path",{"d":"M7 7h10v10"}],["path",{"d":"M7 17 17 7"}]],"Download":[["path",{"d":"M12 15V3"}],["path",{"d":"M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"}],["path",{"d":"m7 10 5 5 5-5"}]],"CodeXml":[["path",{"d":"m18 16 4-4-4-4"}],["path",{"d":"m6 8-4 4 4 4"}],["path",{"d":"m14.5 4-5 16"}]],"Search":[["path",{"d":"m21 21-4.34-4.34"}],["circle",{"cx":"11","cy":"11","r":"8"}]]};
function renderIcons(root = document) {
  root.querySelectorAll("[data-icon]").forEach(placeholder => {
    const nodes = resultIcons[placeholder.dataset.icon];
    if (!nodes) return;
    const ns = "http://www.w3.org/2000/svg";
    const svg = document.createElementNS(ns, "svg");
    Object.entries({viewBox:"0 0 24 24",fill:"none",stroke:"currentColor","stroke-width":1.7,"stroke-linecap":"round","stroke-linejoin":"round","aria-hidden":"true",class:"icon"}).forEach(([key,value]) => svg.setAttribute(key,value));
    nodes.forEach(([tag,attrs]) => {
      const node = document.createElementNS(ns,tag);
      Object.entries(attrs).forEach(([key,value]) => node.setAttribute(key,value));
      svg.appendChild(node);
    });
    placeholder.replaceWith(svg);
  });
}
