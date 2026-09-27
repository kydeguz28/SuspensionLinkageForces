const fs=require('fs'),vm=require('vm'),assert=require('assert');
const html=fs.readFileSync('index.html','utf8');
const payload=JSON.parse(html.match(/<script id="model-data" type="application\/json">([\s\S]*?)<\/script>/)[1]);
const source=fs.readFileSync('viewer_template.html','utf8');
const code=source.slice(source.indexOf('      const plugThreadData ='),source.indexOf('      function renderPlugs()'));
const ctx=vm.createContext({payload,specRevision:'test',localStorage:{getItem:()=>null},sizingRowKey:r=>r.assembly+':'+r.member,assert});
vm.runInContext(code+`
const row={assembly:'front_right',member:'lower_aft',tube_od_in:.375,tube_id_in:.305,chassis_jmx:'JMX3',wheel_jmx:'JMX4'};
const expected={JMX3:[.216607118,7/32],JMX4:[.2708049746,8/28],JMX5:[.3349229895,9/24]};
for(const [size,[minimum,rounded]] of Object.entries(expected)){
 const p=calculatePlug({...row,tube_id_in:.4,tube_od_in:.5,chassis_jmx:size},'chassis_jmx');
 assert(Math.abs(p.required-minimum)<1e-9);assert(Math.abs(p.length-rounded)<1e-5);assert(p.length>=rounded);assert(p.margin>=0);
}
const a=calculatePlug(row,'chassis_jmx'),b=calculatePlug(row,'wheel_jmx');
assert(a.required<b.required);assert(a.weight>0&&b.weight>0);
// Independently evaluate the two cylindrical annuli for the JMX3 plug.
const expectedWeight=.284*Math.PI/4*((.375**2-.1935**2)*.13+(.305**2-.1935**2)*(.21875-.13));
assert(Math.abs(a.weight-expectedWeight)<1e-12);
assert(calculatePlug(row,'wheel_jmx',.2).margin<0);
assert.equal(calculatePlug(row,'wheel_jmx',.1).weight,null);
assert.equal(calculatePlug({...row,wheel_jmx:'JMX5'},'wheel_jmx').valid,false);
assert.equal(calculatePlug({...row,wheel_jmx:'NA'},'wheel_jmx').valid,false);
let count=0;for(const assembly of payload.result.assemblies)for(const member of assembly.sizing_summary){
 if(member.member==='shock')continue;
 for(const end of ['chassis_jmx','wheel_jmx']){const p=calculatePlug(member,end);assert(p.valid);assert(p.margin>=0);count++;}
}assert.equal(count,48);
`,ctx);
console.log('Workbook JMX3/4/5 parity, per-end mapping, mass, short engagement, invalid fit and all 48 defaults passed');
