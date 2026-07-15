const fs = require('fs');
const content = fs.readFileSync('C:/instrument-designer/web/src/data/instruments.ts', 'utf8');
const matches = content.match(/name: "/g);
console.log('Total instruments:', matches ? matches.length : 0);
const names = content.match(/name: "([^"]+)"/g);
if (names) names.forEach((n, i) => console.log((i + 1) + '.', n.replace('name: ', '')));
