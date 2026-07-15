const fs = require('fs');
const content = fs.readFileSync('C:/instrument-designer/web/src/data/instruments.ts', 'utf8');
const instruments = content.split('{').slice(1);
instruments.forEach((inst, i) => {
  const nameMatch = inst.match(/name: "([^"]+)"/);
  const imgMatch = inst.match(/image_url: "([^"]*)"/);
  if (nameMatch && imgMatch) {
    const status = imgMatch[1] === '' ? '❌ EMPTY' : '✅ HAS IMAGE';
    console.log((i+1) + '. ' + status + ' | ' + nameMatch[1]);
  }
});
