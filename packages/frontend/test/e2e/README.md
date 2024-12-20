# Integration Testing

## Local Testing

### Running Tests

To run the tests locally, you can use the following command:

```bash
docker compose --profile test up -d
```	

### Testing with Playwright UI

Writing tests using Playwright UI is a great way to see what's happening in the browser as the test runs. This makes it easier to write and debug tests.

To run the tests with Playwright UI, you need to uncomment the --ui flag in the `docker-compose.yml` file.

```yaml
  integration-tests:
    # ...
    command: npx playwright test --ui
```

Playwright UI uses the DISPLAY Environment variable to locate the X11 server. If you are using Windows you need to install VcXsrv and have it running before starting up docker compose. 

## CI Testing

Tests are run automatically on Gitlab. The configuration for the tests can be found in the `.gitlab-ci.yml` file.
The Tests in the CI pipeline run in headless mode and start with a "fresh" database. Demodata is loaded before the tests are run (see [global-setup.ts](./global-setup.ts)).

### Debugging in CI

Sometimes tests run locally but fail in the CI pipeline. To debug whats happening you can use [Playwright screenshots](https://playwright.dev/docs/screenshots). The screenshots are logged as a base64 encoded string in the console output. To see the screenshot use CyberChef or a similar tools to decode the image.

## Writing Tests

When writing integration tests, try to no use page.waitForTimeout since it makes the tests flaky. Instead, use page.waitForSelector use .waitFor() instead. 

Try to use testIds for selecting elements in the DOM. This makes the tests more robust and less likely to break when the frontend changes.

## Test Data

For Integration tests the Demo Data is loaded into the database before the tests are run. This is done in the [global-setup.ts](./global-setup.ts) file.

To access the IDs of the Demo Data use the [DemoDataState](./util/demo_data.ts) class. Using this class you can also add new IDs for Objects created during the tests.
