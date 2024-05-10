const puppeteer = require('puppeteer');

async function generatePDF() {
    const browser = await puppeteer.launch();
    const page = await browser.newPage();

    // Navigate to the Flask server URL
    await page.goto('http://localhost:5000/qualifying_results', { waitUntil: 'networkidle0' });

    // Wait for a specific element to load
    await page.waitForSelector('.table');

    // Generate PDF
    await page.pdf({ path: 'qualifying_results.pdf', format: 'A4' });

    await browser.close();
}

generatePDF().catch(error => {
    console.error('Error generating PDF:', error);
});
