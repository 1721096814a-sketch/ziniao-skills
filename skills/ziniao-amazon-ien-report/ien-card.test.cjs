const assert = require('assert/strict');
const { buildCard, buildPatchPayload } = require('./scripts/ien-card.cjs');

const store = '2号机欧洲';
const rows = [
  { shipment: 'FBA15TEST01', ien: '26GBTEST00000001', status: '已填写并核对' },
  { shipment: 'FBA15TEST02', ien: '26GBTEST00000002', status: '已填写并核对' },
];
const card = buildCard(store, rows);
assert.equal(card.schema, '2.0');
assert.equal(card.header.title.content, store);
assert.equal(card.header.template, 'green');
const tables = card.body.elements.filter(element => element.tag === 'table');
assert.equal(tables.length, 1);
assert.deepEqual(tables[0].columns.map(column => column.display_name), ['货件编号', 'IEN', '填写状态']);
assert.equal(tables[0].page_size, rows.length);
assert.equal(tables[0].rows.length, 2);
assert.equal(tables[0].rows[0].ien, rows[0].ien);
assert.equal(tables[0].rows[0].status, '已填写并核对');
assert.ok(!JSON.stringify(card).includes('物流说明'));
assert.equal(buildPatchPayload('om_example', store, rows).content, JSON.stringify(card));
assert.equal(buildPatchPayload('om_example', store, rows).content.length <= 30000, true);
for (const badRows of [
  [{ shipment: 'FBA15TEST01', ien: '26GBTEST00000001', status: '已保存，未核对' }],
  [{ shipment: 'FBA15TEST01', ien: '', status: '已填写并核对' }],
  [{ shipment: 'FBA15TEST01', ien: '26GBTEST00000001' }],
]) {
  assert.throws(() => buildCard(store, badRows), /verified|核对|IEN/i);
}
assert.throws(() => buildCard(store, []), /至少|empty/i);
assert.throws(() => buildCard('', rows), /店铺|store/i);
assert.throws(() => buildPatchPayload('', store, rows), /message/i);
// A batch with no successful writes must still report missing source IENs.
const missingRows = [
  { shipment: 'FBA15TEST03', ien: '', status: '未填写：未查询到 IEN' },
  { shipment: 'FBA15TEST04', ien: '', status: '未填写：来源 IEN 为空' },
];
const missingCard = buildCard(store, missingRows);
assert.equal(missingCard.header.title.content, store);
assert.deepEqual(missingCard.body.elements[0].columns.map(column => column.display_name), ['货件编号', 'IEN', '填写状态']);
assert.deepEqual(missingCard.body.elements[0].rows, [
  { shipment: 'FBA15TEST03', ien: '—', status: '未填写：未查询到 IEN' },
  { shipment: 'FBA15TEST04', ien: '—', status: '未填写：来源 IEN 为空' },
]);
const mixedRows = [...rows, ...missingRows];
const mixedCard = buildCard(store, mixedRows);
assert.equal(mixedCard.body.elements[0].rows.length, 4);
assert.equal(mixedCard.body.elements[0].rows[0].status, '已填写并核对');
assert.deepEqual(mixedCard.body.elements[0].rows.slice(2), missingCard.body.elements[0].rows);
const patched = JSON.parse(buildPatchPayload('om_example', store, mixedRows).content);
assert.equal(patched.body.elements[0].rows.length, 4);
for (const status of ['未填写：未查询到 IEN', '未填写：来源 IEN 为空']) {
  assert.throws(() => buildCard(store, [{ shipment: 'FBA15TEST03', ien: '26GBTEST00000003', status }]), /IEN|为空/);
}
assert.throws(() => buildCard(store, [missingRows[0], missingRows[0]]), /重复/);
console.log('PASS: verified, missing-only and mixed batches preserve three columns; patch includes missing rows; invalid success, unknown statuses and contradictory IENs are rejected');
