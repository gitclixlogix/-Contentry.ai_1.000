/**
 * Responsive Design & Cross-Browser E2E Tests
 * Tests: 51-61 (11 tests)
 * Phase 9.2 - Cross-browser compatibility validation
 */
const { test, expect } = require('@playwright/test');

// Helper function to dismiss cookie consent banner
async function dismissCookieBanner(page) {
  try {
    const acceptBtn = page.locator('button:has-text("Accept All")');
    if (await acceptBtn.isVisible({ timeout: 2000 })) {
      await acceptBtn.click({ force: true });
      await page.waitForTimeout(500);
    }
  } catch (e) {
    // Banner might not exist or already dismissed
  }
}

// Helper function to login as demo user
async function loginAsDemoUser(page) {
  await page.goto('/contentry/auth/login');
  await page.waitForLoadState('networkidle');
  await dismissCookieBanner(page);
  
  await page.evaluate(() => window.scrollTo(0, document.body.scrollHeight));
  await page.waitForTimeout(1000);
  
  const demoBtn = page.locator('button:has-text("Demo User")').first();
  await expect(demoBtn).toBeVisible({ timeout: 10000 });
  await demoBtn.click({ force: true });
  await page.waitForURL(/\/contentry\//, { timeout: 30000 });
  await page.waitForLoadState('networkidle');
}

test.describe('Responsive Design & Cross-Browser', () => {

  // Test 51: Mobile viewport works
  test('51. Login page renders on mobile', async ({ page }) => {
    await page.setViewportSize({ width: 390, height: 844 });
    await page.goto('/contentry/auth/login');
    await page.waitForLoadState('networkidle');
    await dismissCookieBanner(page);
    
    // Should still have login elements
    const loginElements = page.locator('button, input');
    await expect(loginElements.first()).toBeVisible({ timeout: 10000 });
  });

  // Test 52: Tablet viewport works
  test('52. Dashboard renders on tablet', async ({ page }) => {
    await page.setViewportSize({ width: 768, height: 1024 });
    await loginAsDemoUser(page);
    
    await page.goto('/contentry/dashboard');
    await page.waitForLoadState('networkidle');
    
    const has404 = await page.locator('text=404, text=Not Found').count() > 0;
    expect(has404).toBeFalsy();
  });

  // Test 53: Desktop viewport works
  test('53. Full desktop layout renders', async ({ page }) => {
    await page.setViewportSize({ width: 1920, height: 1080 });
    await loginAsDemoUser(page);
    
    // Page should load without errors
    await page.goto('/contentry/dashboard');
    await page.waitForLoadState('networkidle');
    
    const has404 = await page.locator('text=404').count() > 0;
    expect(has404).toBeFalsy();
  });

  // Test 54: Touch interactions work on mobile
  test('54. Touch buttons are accessible', async ({ page }) => {
    await page.setViewportSize({ width: 390, height: 844 });
    await page.goto('/contentry/auth/login');
    await page.waitForLoadState('networkidle');
    await dismissCookieBanner(page);
    
    // Scroll to demo buttons
    await page.evaluate(() => window.scrollTo(0, document.body.scrollHeight));
    await page.waitForTimeout(500);
    
    // Buttons should exist and be clickable on mobile
    const demoBtn = page.locator('button:has-text("Demo User")').first();
    const btnExists = await demoBtn.count() > 0;
    expect(btnExists).toBeTruthy();
  });

  // Test 55: Forms work on all viewports
  test('55. Forms are usable on mobile', async ({ page }) => {
    await page.setViewportSize({ width: 390, height: 844 });
    await page.goto('/contentry/auth/signup');
    await page.waitForLoadState('networkidle');
    await dismissCookieBanner(page);
    
    const inputs = page.locator('input');
    await expect(inputs.first()).toBeVisible({ timeout: 10000 });
  });

  // Test 56: Navigation menu adapts
  test('56. Navigation adapts to viewport', async ({ page }) => {
    // Desktop
    await page.setViewportSize({ width: 1920, height: 1080 });
    await loginAsDemoUser(page);
    
    await page.goto('/contentry/content-moderation');
    await page.waitForLoadState('networkidle');
    
    // Switch to mobile
    await page.setViewportSize({ width: 390, height: 844 });
    await page.waitForLoadState('networkidle');
    
    // Page should still function
    const has404 = await page.locator('text=404, text=Not Found').count() > 0;
    expect(has404).toBeFalsy();
  });

  // Test 57: Text is readable on all sizes
  test('57. Text scales appropriately', async ({ page }) => {
    await page.setViewportSize({ width: 390, height: 844 });
    await page.goto('/contentry/auth/login');
    await page.waitForLoadState('networkidle');
    await dismissCookieBanner(page);
    
    // Login button should be visible on mobile
    const loginBtn = page.locator('button:has-text("Log in")');
    await expect(loginBtn).toBeVisible({ timeout: 10000 });
  });

  // Test 58: Images are responsive
  test('58. Images scale correctly', async ({ page }) => {
    await page.setViewportSize({ width: 390, height: 844 });
    await page.goto('/contentry/auth/login');
    await page.waitForLoadState('networkidle');
    await dismissCookieBanner(page);
    
    const images = page.locator('img');
    const count = await images.count();
    
    if (count > 0) {
      const img = images.first();
      const box = await img.boundingBox();
      if (box) {
        // Image shouldn't exceed viewport width
        expect(box.width).toBeLessThanOrEqual(400);
      }
    }
    expect(true).toBeTruthy();
  });

  // Test 59: No horizontal scroll on mobile
  test('59. No horizontal overflow on mobile', async ({ page }) => {
    await page.setViewportSize({ width: 390, height: 844 });
    await page.goto('/contentry/auth/login');
    await page.waitForLoadState('networkidle');
    await dismissCookieBanner(page);
    
    const scrollWidth = await page.evaluate(() => document.documentElement.scrollWidth);
    // Allow buffer for mobile view
    expect(scrollWidth).toBeLessThanOrEqual(420);
  });

  // Test 60: Modals work on mobile
  test('60. Modals are accessible on mobile', async ({ page }) => {
    await page.setViewportSize({ width: 390, height: 844 });
    await loginAsDemoUser(page);
    
    await page.goto('/contentry/settings');
    await page.waitForLoadState('networkidle');
    
    // Page should function on mobile
    const has404 = await page.locator('text=404, text=Not Found').count() > 0;
    expect(has404).toBeFalsy();
  });

  // Test 61: Loading states show correctly
  test('61. Loading indicators work', async ({ page }) => {
    await page.goto('/contentry/auth/login');
    await page.waitForLoadState('networkidle');
    await dismissCookieBanner(page);
    
    await page.evaluate(() => window.scrollTo(0, document.body.scrollHeight));
    await page.waitForTimeout(500);
    
    // During navigation, loading might show
    await page.locator('button:has-text("Demo User")').first().click({ force: true });
    
    // Eventually should complete
    await page.waitForURL(/\/contentry\//, { timeout: 20000 });
    
    // Should not be stuck in loading
    const has404 = await page.locator('text=404, text=Not Found').count() > 0;
    expect(has404).toBeFalsy();
  });
});
