const fs = require('fs'), vm = require('vm'), assert = require('assert');
const html = fs.readFileSync('index.html','utf8');
const payload = JSON.parse(html.match(/<script id="model-data" type="application\/json">([\s\S]*?)<\/script>/)[1]);
const source = fs.readFileSync('viewer_template.html','utf8');
const code = source.slice(source.indexOf('      const sizingRows ='),source.indexOf('      function renderMethodsMetadata'));
const storage = {
  'bfr-jmx-specs-v1': JSON.stringify({'rear:pushrod':{chassis_jmx:'JMX3'}}),
  'bfr-tube-specs-v1': JSON.stringify({'rear_right:lower_fore':{tube_od_in:.25,tube_id_in:.24}})
};
const context = vm.createContext({payload, configAssemblies:payload.config.assemblies, localStorage:{getItem:k=>storage[k],setItem:(k,v)=>storage[k]=v}, assert});
vm.runInContext(code + `
assert.equal(migrateRodSpecKeys({'front:pullrod':{chassis_jmx:'JMX5'}})['front:pushrod'].chassis_jmx,'JMX5');
assert.equal(migrateRodSpecKeys({'front_right:pullrod':{tube_od_in:.5}})['front_right:pushrod'].tube_od_in,.5);
const row = sizingRows.find(r => r.assembly === 'rear_right' && r.member === 'pushrod');
const opposite = sizingRows.find(r => r.assembly === 'rear_left' && r.member === 'pushrod');
assert.equal(row.chassis_jmx, 'JMX4');
assert.equal(Object.keys(savedTubeSpecs).length, 0);
assert.equal(Object.keys(savedJmxSpecs).length, 0);
const originalWheel = row.wheel_jmx;
const originalChecks = JSON.stringify(row.hardware_checks.filter(c => c.connection === 'wheel'));
savedJmxSpecs[jmxKey(row)] = {chassis_jmx:'JMX5'};
applySavedJmxSpecs();
assert.equal(row.chassis_jmx, 'JMX5'); assert.equal(opposite.chassis_jmx, 'JMX5');
assert.equal(row.wheel_jmx, originalWheel);
assert.equal(JSON.stringify(row.hardware_checks.filter(c => c.connection === 'wheel')),originalChecks);
assert(row.hardware_checks.filter(c=>c.connection==='chassis').every(c=>c.selection==='JMX5'));
assert.equal(row.chassis_jmx_margin,jmxVariants[sizingRowKey(row)].JMX5.chassis_jmx_margin);
const selectedMargin = row.chassis_jmx_margin;
recalculateTubeRow(row,.625,.5);
assert.equal(row.chassis_jmx_margin,selectedMargin);
persistJmxSpecs(); assert(JSON.parse(localStorage.getItem(jmxStorageKey))['rear:pushrod'].chassis_jmx === 'JMX5');
applyJmxEnd(row,'wheel_jmx','JMX4');assert.equal(row.chassis_jmx,'JMX5');assert.equal(row.wheel_jmx,'JMX4');
`,context);
console.log('JMX independent-end, mirrored, hardware, tube interaction, and persistence checks passed');
