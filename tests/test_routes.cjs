const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
const src=fs.readFileSync('templates/player.html','utf8');
const code=src.slice(src.indexOf('const programId ='),src.indexOf('let loadSerial ='));
const base='https://example.test/myradio/';
for(const [path,expected] of [
  ['aviation/2026-11-06/ja/',['aviation','2026-11-06','ja']],
  ['aviation/2026-11-06/ja/index.html',['aviation','2026-11-06','ja']],
  ['#aviation/2026-11-06/ja',['aviation','2026-11-06','ja']],
  ['#2026-11-06/ja',['aviation','2026-11-06','ja']],
  ['singapore-economy/2026-11-07/ja/',['singapore-economy','2026-11-07','ja']],
  ['#singapore-economy/2026-11-06/ja',['singapore-economy','2026-11-06','ja']],
  ['', ['aviation',null,null]],
]) {
  const ctx={URL,STATION:{program:{id:'aviation'},language:'ja'},LANG:'ja',APP_BASE:new URL(base),location:new URL(path,base)};
  vm.createContext(ctx);vm.runInContext(code,ctx);
  const actual=JSON.parse(vm.runInContext('JSON.stringify(parseEpisodeLocation())',ctx));
  assert.deepEqual([actual.program,actual.date??null,actual.lang??null],expected);
  assert.equal(vm.runInContext('episodeUrl("2026-11-06","ja")',ctx),'/myradio/aviation/2026-11-06/ja/');
}
console.log('PASS: direct episode paths, index.html, legacy hashes, root and subdirectory URLs');

const memory = new Map([['news-radio:pos', '{"2026-11-07-ja":42}']]);
const ctx = { STATION:{program:{id:'aviation'}}, localStorage:{getItem:k=>memory.get(k), setItem:(k,v)=>memory.set(k,v)} };
vm.createContext(ctx);
vm.runInContext('const programId = () => STATION.program.id;\n' + src.slice(src.indexOf('const store ='),src.indexOf('let curName =')),ctx);
assert.equal(vm.runInContext('store("pos")["2026-11-07-ja"]',ctx),42);
ctx.STATION.program.id = 'singapore-economy';
assert.equal(vm.runInContext('Object.keys(store("pos")).length',ctx),0);
vm.runInContext('store("pos", {"2026-11-07-ja":17}); store("heard", {"2026-11-07":1})',ctx);
ctx.STATION.program.id = 'aviation';
assert.equal(vm.runInContext('store("pos")["2026-11-07-ja"]',ctx),42);
assert.equal(vm.runInContext('Object.keys(store("heard")).length',ctx),0);
console.log('PASS: same-date positions and heard state isolated; existing aviation history retained');
