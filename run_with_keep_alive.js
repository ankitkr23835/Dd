const puppeteer = require('puppeteer');
const { exec } = require('child_process');

(async () => {
  const browser = await puppeteer.launch({ headless: true });
  const page = await browser.newPage();
  await page.goto('https://www.example.com', { waitUntil: 'domcontentloaded' });

  // Run the keep_alive.py script in the background
  exec('python keep_alive.py', (error, stdout, stderr) => {
    if (error) {
      console.error(`Error: ${error}`);
      return;
    }
    console.log(`stdout: ${stdout}`);
    console.error(`stderr: ${stderr}`);
  });
})();
