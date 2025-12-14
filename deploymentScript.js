const { log } = require("console");
const fs = require("fs");
const fileBlacklist = [
    /\.github/,
    /\.git/,
    /media/,
    /.*\.js/,
    /tools/
];
const deployFolder = "../1444StartReadyForPublish";

if (fs.existsSync(deployFolder)) fs.rmSync(deployFolder, { recursive: true, force: true });
fs.mkdirSync(deployFolder);

const fileList = fs.readdirSync("./");
for (const file of fileList) {
    let isBlacklisted = false;
    for (const blackItem of fileBlacklist) {
        if (blackItem.test(file)) {
            
            isBlacklisted = true;
        }
    }
    if (!isBlacklisted) fs.cpSync(file, deployFolder + "/" + file, { recursive: true });
}