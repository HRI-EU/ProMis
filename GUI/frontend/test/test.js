const {By, Builder, until} = require('selenium-webdriver');
const assert = require("assert");
const path = require("path");
const fs = require("fs");

async function functionalTest(browser, done) {
  // setup the reference data
  const filePath = './test/testPortability.csv';

  let driver;
  
  try {
    // create driver
    driver = await new Builder().forBrowser(browser).build();
    // set implicit wait to 10 seconds
    await driver.manage().setTimeouts({implicit: 10000});
    // navigate to the app
    await driver.get('http://localhost:3000/');
    // maximize the window
    await driver.manage().window().maximize();

    // get the file path
    const data = path.resolve(filePath);

    // reveal the sidebar
    await driver.findElement(By.id("sidebar-right-fab")).click();

    // Upload file
    await driver.findElement(By.id("csv-reader-input")).sendKeys(data);
    
    // wait for the layer to be rendered
    await driver.wait(until.elementLocated(By.id("layer-0")), 10000);

    // check the leaflet canvas overlay is rendered
    const canvas = await driver.findElement(By.css(".leaflet-overlay-pane canvas"));
    // assert the canvas is rendered
    assert(canvas);

    // get the layer
    const layer = await driver.findElement(By.id("layer-0"));
    // assert the layer is rendered
    assert(layer);

    done();
  } catch (e) {
    console.log(e)
    done(e);
  } finally {
    await driver.quit();
  }
}

const browsers = ["chrome", "firefox", "MicrosoftEdge"];

browsers.forEach((browser) => {
  describe(browser, function () {
    this.timeout(10000); // Set timeout to 10 seconds, instead of the original 2 seconds
    it('should render and revel properties when click', function (done) {
      functionalTest(browser, done);
    });
  });
});