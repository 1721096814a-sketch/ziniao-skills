'use strict';

const fs = require('node:fs');

function buildCard(store, rows) {
  if (typeof store !== 'string' || !store.trim()) throw new Error('需要店铺名称 store');
  if (!Array.isArray(rows) || !rows.length) throw new Error('至少需要一个有明确结果的货件，不能发送 empty 卡片');
  const missingStatuses = new Set(['未填写：未查询到 IEN', '未填写：来源 IEN 为空']);
  const seen = new Set();
  const records = rows.map(row => {
    const missingIen = missingStatuses.has(row.status);
    if (row.status !== '已填写并核对' && !missingIen) throw new Error('只接受已填写并核对或明确未查询到 IEN / 来源 IEN 为空的记录');
    if (typeof row.shipment !== 'string' || !/^FBA[A-Z0-9]+$/.test(row.shipment)) throw new Error('需要真实 FBA 货件编号');
    if (typeof row.ien !== 'string') throw new Error('IEN 必须是字符串，未查询到时传空字符串');
    const ien = row.ien.trim();
    if (missingIen && ien) throw new Error('未查询到 IEN / 来源 IEN 为空的记录必须传空 IEN');
    if (!missingIen && !ien) throw new Error('已填写并核对的 IEN 不可为空');
    if (seen.has(row.shipment)) throw new Error('同一店铺货件编号重复，需先核对');
    seen.add(row.shipment);
    return { shipment: row.shipment, ien: missingIen ? '—' : ien, status: row.status };
  });
  const card = {
    schema: '2.0',
    config: { width_mode: 'fill' },
    header: { title: { tag: 'plain_text', content: store.trim() }, template: 'green' },
    body: {
      elements: [{
        tag: 'table',
        page_size: Math.min(records.length, 10),
        row_height: 'auto',
        header_style: { bold: true, background_style: 'grey', lines: 1 },
        columns: [
          { name: 'shipment', display_name: '货件编号', data_type: 'text', width: '30%' },
          { name: 'ien', display_name: 'IEN', data_type: 'text', width: '45%' },
          { name: 'status', display_name: '填写状态', data_type: 'text', width: '25%' },
        ],
        rows: records,
      }],
    },
  };
  if (Buffer.byteLength(JSON.stringify(card), 'utf8') > 30000) throw new Error('卡片超过 30 KB，按店铺和批次拆分后再发送');
  return card;
}

function buildPatchPayload(messageId, store, rows) {
  if (typeof messageId !== 'string' || !messageId.startsWith('om_')) throw new Error('需要当前批次的真实 message_id');
  return { content: JSON.stringify(buildCard(store, rows)) };
}

module.exports = { buildCard, buildPatchPayload };

if (require.main === module) {
  try {
    const [input, mode, messageId, ...extra] = process.argv.slice(2);
    if (!input || (mode && mode !== '--patch') || (mode === '--patch' && !messageId) || extra.length) {
      throw new Error('用法: node ien-card.cjs <input.json|-> [--patch om_message_id]');
    }
    const { store, rows } = JSON.parse(fs.readFileSync(input === '-' ? 0 : input, 'utf8').replace(/^﻿/, ''));
    const result = mode === '--patch' ? buildPatchPayload(messageId, store, rows) : buildCard(store, rows);
    process.stdout.write(JSON.stringify(result) + '\n');
  } catch (error) {
    process.stderr.write(error.message + '\n');
    process.exitCode = 1;
  }
}
