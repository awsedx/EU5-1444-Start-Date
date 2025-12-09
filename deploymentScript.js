const { log } = require("console");
const fs = require("fs");
const fileBlacklist = [
    /\.github/,
    /\.git/,
    /media/,
    /.*\.js/
];
const deployFolder = "../1444StartReadyForPublish";

if (fs.existsSync(deployFolder)) fs.rmSync(deployFolder, { recursive: true, force: true });
fs.mkdirSync(deployFolder);

const fileList = fs.readdirSync("./");
for (const file of fileList) {
    console.log(file);
    
    let isBlacklisted = false;
    for (const blackItem of fileBlacklist) {
        console.log(blackItem.test(file));
        
        if (blackItem.test(file)) {
            
            isBlacklisted = true;
        }
    }
    if (!isBlacklisted) fs.cpSync(file, deployFolder + "/" + file, { recursive: true });
}