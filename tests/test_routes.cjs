const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
const src=fs.readFileSync('templates/player.html','utf8');
const code=src.slice(src.indexOf('const programId ='),src.indexOf('let loadSerial ='));
const base='https://example.test/myradio/';
for(const [path,expected] of [
  ['aviation/2026-11-06/ja/',['aviation','2026-11-06','ja']],
  ['aviation/2026-11-06/ja/index.html',['aviation','2026-11-06','ja']],
  ['#aviation/2026-11-06/ja',['aviation','2026-11-06','ja']],
  ['#2026-11-06/ja',['aviation','2026-11-06','ja']],
  ['', ['aviation',null,null]],
]) {
  const ctx={URL,STATION:{program:{id:'aviation'},language:'ja'},LANG:'ja',APP_BASE:new URL(base),location:new URL(path,base)};
  vm.createContext(ctx);vm.runInContext(code,ctx);
  const actual=JSON.parse(vm.runInContext('JSON.stringify(parseEpisodeLocation())',ctx));
  assert.deepEqual([actual.program,actual.date??null,actual.lang??null],expected);
  assert.equal(vm.runInContext('episodeUrl("2026-11-06","ja")',ctx),'/myradio/aviation/2026-11-06/ja/');
}
console.log('PASS: direct episode paths, index.html, legacy hashes, root and subdirectory URLs');
