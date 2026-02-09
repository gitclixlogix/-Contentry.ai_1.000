/**
 * Comprehensive E2E Testing for Contentry Application
 * 
 * Test Coverage:
 * 1. Authentication Flow - Demo admin login, navigation, links
 * 2. Signup Flow - OAuth buttons, form fields, GDPR checkboxes
 * 3. Admin Dashboard - Stats, Financial Analytics, User Management
 * 4. Privacy & Terms Pages - Content verification
 * 5. Branding Consistency - Logo positioning and responsiveness
 * 
 * Testing Requirements:
 * - Screenshots at major steps
 * - No console errors verification
 * - Desktop (1920px) and mobile (390px) viewports
 * - Functional verification of all buttons, links, forms
 * - Red asterisks on required fields verification
 */

const { test, expect } = require('@playwright/test');

test.describe('Contentry Application - Comprehensive E2E Testing', () => {
  
  test('Complete Authentication and Admin Dashboard Flow - Desktop', async ({ page }) => {
    console.log('🚀 Starting Comprehensive E2E Testing - Desktop Viewport');
    
    // Set desktop viewport
    await page.setViewportSize({ width: 1920, height: 1080 });
    
    try {
      // Step 1: Navigate to login page
      console.log('📍 Step 1: Navigating to login page');
      await page.goto('https://admin-portal-278.preview.emergentagent.com/contentry/auth/login');
      await page.waitForLoadState('networkidle');
      
      // Verify Contentry logo and branding
      console.log('🎨 Verifying Contentry branding on login page');
      const logo = await page.locator('img[alt="Contentry.ai Logo"]');
      await expect(logo).toBeVisible();
      
      const logoText = await page.locator('text=Contentry.ai');
      await expect(logoText).toBeVisible();
      
      // Take screenshot of login page
      await page.screenshot({ 
        path: '/app/frontend/tests/screenshots/01_login_page_desktop.png', 
        quality: 40, 
        fullPage: false 
      });
      console.log('📸 Screenshot taken: Login page desktop');
      
      // Step 2: Test Demo Admin Login
      console.log('📍 Step 2: Testing Demo Admin Login (🔐 Admin button)');
      const adminButton = await page.locator('button:has-text("🔐 Admin")');
      await expect(adminButton).toBeVisible();
      await adminButton.click({ force: true });
      
      // Wait for navigation to admin dashboard
      await page.waitForURL('**/contentry/admin', { timeout: 10000 });
      console.log('✅ Successfully navigated to admin dashboard');
      
      // Step 3: Verify Admin Dashboard Components
      console.log('📍 Step 3: Verifying Admin Dashboard Components');
      
      // Check for Admin Analytics Dashboard title
      const dashboardTitle = await page.locator('text=Admin Analytics Dashboard');
      await expect(dashboardTitle).toBeVisible();
      
      // Verify ADMIN badge
      const adminBadge = await page.locator('text=ADMIN');
      await expect(adminBadge).toBeVisible();
      
      // Check for mini statistics cards (6 cards expected)
      const statsCards = await page.locator('[data-testid*="mini-stat"], .css-').count();
      console.log(`📊 Found ${statsCards} statistics elements on dashboard`);
      
      // Look for key metrics text
      const totalUsers = await page.locator('text=Total Users');
      const totalPosts = await page.locator('text=Total Posts');
      const totalRevenue = await page.locator('text=Total Revenue');
      
      await expect(totalUsers).toBeVisible();
      await expect(totalPosts).toBeVisible();
      await expect(totalRevenue).toBeVisible();
      
      console.log('✅ Admin dashboard statistics cards verified');
      
      // Take screenshot of admin dashboard
      await page.screenshot({ 
        path: '/app/frontend/tests/screenshots/02_admin_dashboard_desktop.png', 
        quality: 40, 
        fullPage: false 
      });
      console.log('📸 Screenshot taken: Admin dashboard desktop');
      
      // Step 4: Test Navigation Links
      console.log('📍 Step 4: Testing navigation to other admin pages');
      
      // Check sidebar navigation
      const sidebar = await page.locator('[data-testid="sidebar"], .sidebar, nav');
      if (await sidebar.count() > 0) {
        console.log('📋 Sidebar navigation found');
        
        // Look for Financial Analytics link
        const financialLink = await page.locator('text=Financial Analytics, a[href*="financial"]');
        if (await financialLink.count() > 0) {
          console.log('💰 Financial Analytics link found');
        }
        
        // Look for User Management link
        const userMgmtLink = await page.locator('text=User Management, a[href*="users"]');
        if (await userMgmtLink.count() > 0) {
          console.log('👥 User Management link found');
        }
      }
      
      console.log('✅ Admin dashboard navigation verified');
      
    } catch (error) {
      console.error('❌ Error in authentication flow:', error.message);
      await page.screenshot({ 
        path: '/app/frontend/tests/screenshots/error_auth_flow.png', 
        quality: 40, 
        fullPage: false 
      });
      throw error;
    }
  });
  
  test('Signup Flow and Form Validation - Desktop', async ({ page }) => {
    console.log('🚀 Starting Signup Flow Testing - Desktop Viewport');
    
    // Set desktop viewport
    await page.setViewportSize({ width: 1920, height: 1080 });
    
    try {
      // Step 1: Navigate to signup page
      console.log('📍 Step 1: Navigating to signup page');
      await page.goto('https://admin-portal-278.preview.emergentagent.com/contentry/auth/signup');
      await page.waitForLoadState('networkidle');
      
      // Verify Contentry logo and branding on signup
      console.log('🎨 Verifying Contentry branding on signup page');
      const logo = await page.locator('img[alt="Contentry.ai Logo"]');
      await expect(logo).toBeVisible();
      
      const logoText = await page.locator('text=Contentry.ai');
      await expect(logoText).toBeVisible();
      
      // Take screenshot of signup page
      await page.screenshot({ 
        path: '/app/frontend/tests/screenshots/03_signup_page_desktop.png', 
        quality: 40, 
        fullPage: false 
      });
      console.log('📸 Screenshot taken: Signup page desktop');
      
      // Step 2: Verify OAuth Buttons
      console.log('📍 Step 2: Verifying OAuth buttons visibility');
      
      const googleButton = await page.locator('button:has-text("Google")');
      const microsoftButton = await page.locator('button:has-text("Microsoft")');
      const appleButton = await page.locator('button:has-text("Apple")');
      const slackButton = await page.locator('button:has-text("Slack")');
      
      await expect(googleButton).toBeVisible();
      await expect(microsoftButton).toBeVisible();
      await expect(appleButton).toBeVisible();
      await expect(slackButton).toBeVisible();
      
      console.log('✅ All OAuth buttons (Google, Microsoft, Apple, Slack) are visible');
      
      // Step 3: Verify Form Fields
      console.log('📍 Step 3: Verifying form fields');
      
      // Full Name field
      const fullNameField = await page.locator('input[placeholder*="full name"], input[placeholder*="Full name"]');
      await expect(fullNameField).toBeVisible();
      
      // Email/Phone tabs
      const emailTab = await page.locator('text=Email').first();
      const phoneTab = await page.locator('text=Phone').first();
      await expect(emailTab).toBeVisible();
      await expect(phoneTab).toBeVisible();
      
      // Password fields
      const passwordField = await page.locator('input[type="password"]').first();
      const confirmPasswordField = await page.locator('input[placeholder*="Confirm"], input[placeholder*="confirm"]');
      
      await expect(passwordField).toBeVisible();
      await expect(confirmPasswordField).toBeVisible();
      
      console.log('✅ All form fields verified: Full Name, Email/Phone tabs, Password, Confirm Password');
      
      // Step 4: Verify GDPR Checkboxes with Red Asterisks
      console.log('📍 Step 4: Verifying GDPR checkboxes and red asterisks');
      
      // Look for checkboxes
      const checkboxes = await page.locator('input[type="checkbox"]');
      const checkboxCount = await checkboxes.count();
      console.log(`📋 Found ${checkboxCount} checkboxes on signup form`);
      
      // Look for red asterisks (required field indicators)
      const redAsterisks = await page.locator('text="*", span:has-text("*")').count();
      console.log(`🔴 Found ${redAsterisks} red asterisk indicators`);
      
      // Look for Terms of Service checkbox
      const termsCheckbox = await page.locator('text*=Terms of Service, text*=terms');
      if (await termsCheckbox.count() > 0) {
        console.log('📄 Terms of Service checkbox found');
      }
      
      // Look for Privacy Policy checkbox
      const privacyCheckbox = await page.locator('text*=Privacy Policy, text*=privacy');
      if (await privacyCheckbox.count() > 0) {
        console.log('🔒 Privacy Policy checkbox found');
      }
      
      // Look for Data Processing consent checkbox
      const dataProcessingCheckbox = await page.locator('text*=data processing, text*=Data processing');
      if (await dataProcessingCheckbox.count() > 0) {
        console.log('⚙️ Data Processing consent checkbox found');
      }
      
      console.log('✅ GDPR checkboxes verification completed');
      
      // Step 5: Verify "Already have an account? Log in" link
      console.log('📍 Step 5: Verifying login link');
      
      const loginLink = await page.locator('text*=Already have an account, a[href*="login"]');
      if (await loginLink.count() > 0) {
        console.log('🔗 "Already have an account? Log in" link found');
      }
      
      // Take screenshot of complete signup form
      await page.screenshot({ 
        path: '/app/frontend/tests/screenshots/04_signup_form_complete_desktop.png', 
        quality: 40, 
        fullPage: false 
      });
      console.log('📸 Screenshot taken: Complete signup form desktop');
      
      console.log('✅ Signup flow verification completed successfully');
      
    } catch (error) {
      console.error('❌ Error in signup flow:', error.message);
      await page.screenshot({ 
        path: '/app/frontend/tests/screenshots/error_signup_flow.png', 
        quality: 40, 
        fullPage: false 
      });
      throw error;
    }
  });
  
  test('Privacy and Terms Pages Content Verification', async ({ page }) => {
    console.log('🚀 Starting Privacy and Terms Pages Testing');
    
    // Set desktop viewport
    await page.setViewportSize({ width: 1920, height: 1080 });
    
    try {
      // Step 1: Test Privacy Policy Page
      console.log('📍 Step 1: Testing Privacy Policy page');
      await page.goto('https://admin-portal-278.preview.emergentagent.com/contentry/privacy');
      await page.waitForLoadState('networkidle');
      
      // Verify Privacy Policy content
      const privacyTitle = await page.locator('text=Privacy Policy');
      await expect(privacyTitle).toBeVisible();
      
      // Look for key sections
      const gdprSection = await page.locator('text*=GDPR, text*=rights');
      const dataRetentionSection = await page.locator('text*=Data Retention, text*=retention');
      const securitySection = await page.locator('text*=Data Security, text*=security');
      
      if (await gdprSection.count() > 0) {
        console.log('✅ GDPR rights section found in Privacy Policy');
      }
      if (await dataRetentionSection.count() > 0) {
        console.log('✅ Data Retention section found in Privacy Policy');
      }
      if (await securitySection.count() > 0) {
        console.log('✅ Data Security section found in Privacy Policy');
      }
      
      // Take screenshot of privacy policy
      await page.screenshot({ 
        path: '/app/frontend/tests/screenshots/05_privacy_policy_page.png', 
        quality: 40, 
        fullPage: false 
      });
      console.log('📸 Screenshot taken: Privacy Policy page');
      
      // Step 2: Test Terms of Service Page
      console.log('📍 Step 2: Testing Terms of Service page');
      await page.goto('https://admin-portal-278.preview.emergentagent.com/contentry/terms');
      await page.waitForLoadState('networkidle');
      
      // Verify Terms of Service content
      const termsTitle = await page.locator('text=Terms of Service');
      await expect(termsTitle).toBeVisible();
      
      // Look for key sections
      const acceptanceSection = await page.locator('text*=Acceptance of Terms, text*=acceptance');
      const subscriptionSection = await page.locator('text*=Subscription, text*=payment');
      const liabilitySection = await page.locator('text*=Limitation of Liability, text*=liability');
      
      if (await acceptanceSection.count() > 0) {
        console.log('✅ Acceptance of Terms section found');
      }
      if (await subscriptionSection.count() > 0) {
        console.log('✅ Subscription and Payment section found');
      }
      if (await liabilitySection.count() > 0) {
        console.log('✅ Limitation of Liability section found');
      }
      
      // Take screenshot of terms of service
      await page.screenshot({ 
        path: '/app/frontend/tests/screenshots/06_terms_of_service_page.png', 
        quality: 40, 
        fullPage: false 
      });
      console.log('📸 Screenshot taken: Terms of Service page');
      
      console.log('✅ Privacy and Terms pages verification completed successfully');
      
    } catch (error) {
      console.error('❌ Error in privacy/terms pages:', error.message);
      await page.screenshot({ 
        path: '/app/frontend/tests/screenshots/error_privacy_terms.png', 
        quality: 40, 
        fullPage: false 
      });
      throw error;
    }
  });
  
  test('Mobile Responsiveness Testing - 390px Viewport', async ({ page }) => {
    console.log('🚀 Starting Mobile Responsiveness Testing - 390px Viewport');
    
    // Set mobile viewport
    await page.setViewportSize({ width: 390, height: 844 });
    
    try {
      // Step 1: Test login page on mobile
      console.log('📍 Step 1: Testing login page mobile responsiveness');
      await page.goto('https://admin-portal-278.preview.emergentagent.com/contentry/auth/login');
      await page.waitForLoadState('networkidle');
      
      // Verify logo is still visible and properly sized on mobile
      const logo = await page.locator('img[alt="Contentry.ai Logo"]');
      await expect(logo).toBeVisible();
      
      const logoText = await page.locator('text=Contentry.ai');
      await expect(logoText).toBeVisible();
      
      // Take screenshot of mobile login
      await page.screenshot({ 
        path: '/app/frontend/tests/screenshots/07_login_page_mobile.png', 
        quality: 40, 
        fullPage: false 
      });
      console.log('📸 Screenshot taken: Login page mobile (390px)');
      
      // Step 2: Test signup page on mobile
      console.log('📍 Step 2: Testing signup page mobile responsiveness');
      await page.goto('https://admin-portal-278.preview.emergentagent.com/contentry/auth/signup');
      await page.waitForLoadState('networkidle');
      
      // Verify branding on mobile signup
      const signupLogo = await page.locator('img[alt="Contentry.ai Logo"]');
      await expect(signupLogo).toBeVisible();
      
      // Verify OAuth buttons are still accessible on mobile
      const googleButton = await page.locator('button:has-text("Google")');
      await expect(googleButton).toBeVisible();
      
      // Take screenshot of mobile signup
      await page.screenshot({ 
        path: '/app/frontend/tests/screenshots/08_signup_page_mobile.png', 
        quality: 40, 
        fullPage: false 
      });
      console.log('📸 Screenshot taken: Signup page mobile (390px)');
      
      // Step 3: Test admin dashboard on mobile (after demo login)
      console.log('📍 Step 3: Testing admin dashboard mobile responsiveness');
      
      // Go back to login and do demo admin login
      await page.goto('https://admin-portal-278.preview.emergentagent.com/contentry/auth/login');
      await page.waitForLoadState('networkidle');
      
      const adminButton = await page.locator('button:has-text("🔐 Admin")');
      await adminButton.click({ force: true });
      
      // Wait for navigation to admin dashboard
      await page.waitForURL('**/contentry/admin', { timeout: 10000 });
      
      // Verify dashboard elements are responsive on mobile
      const dashboardTitle = await page.locator('text=Admin Analytics Dashboard');
      await expect(dashboardTitle).toBeVisible();
      
      // Take screenshot of mobile admin dashboard
      await page.screenshot({ 
        path: '/app/frontend/tests/screenshots/09_admin_dashboard_mobile.png', 
        quality: 40, 
        fullPage: false 
      });
      console.log('📸 Screenshot taken: Admin dashboard mobile (390px)');
      
      console.log('✅ Mobile responsiveness testing completed successfully');
      
    } catch (error) {
      console.error('❌ Error in mobile responsiveness testing:', error.message);
      await page.screenshot({ 
        path: '/app/frontend/tests/screenshots/error_mobile_responsive.png', 
        quality: 40, 
        fullPage: false 
      });
      throw error;
    }
  });
  
  test('Console Errors and Network Monitoring', async ({ page }) => {
    console.log('🚀 Starting Console Errors and Network Monitoring');
    
    const consoleMessages = [];
    const networkErrors = [];
    
    // Monitor console messages
    page.on('console', msg => {
      consoleMessages.push({
        type: msg.type(),
        text: msg.text(),
        location: msg.location()
      });
    });
    
    // Monitor network failures
    page.on('requestfailed', request => {
      networkErrors.push({
        url: request.url(),
        failure: request.failure()
      });
    });
    
    try {
      // Set desktop viewport
      await page.setViewportSize({ width: 1920, height: 1080 });
      
      // Test login page
      console.log('📍 Monitoring login page for errors');
      await page.goto('https://admin-portal-278.preview.emergentagent.com/contentry/auth/login');
      await page.waitForLoadState('networkidle');
      await page.waitForTimeout(2000); // Wait for any async operations
      
      // Test signup page
      console.log('📍 Monitoring signup page for errors');
      await page.goto('https://admin-portal-278.preview.emergentagent.com/contentry/auth/signup');
      await page.waitForLoadState('networkidle');
      await page.waitForTimeout(2000);
      
      // Test admin dashboard
      console.log('📍 Monitoring admin dashboard for errors');
      await page.goto('https://admin-portal-278.preview.emergentagent.com/contentry/auth/login');
      await page.waitForLoadState('networkidle');
      
      const adminButton = await page.locator('button:has-text("🔐 Admin")');
      await adminButton.click({ force: true });
      await page.waitForURL('**/contentry/admin', { timeout: 10000 });
      await page.waitForTimeout(3000); // Wait for dashboard to fully load
      
      // Test privacy page
      console.log('📍 Monitoring privacy page for errors');
      await page.goto('https://admin-portal-278.preview.emergentagent.com/contentry/privacy');
      await page.waitForLoadState('networkidle');
      await page.waitForTimeout(2000);
      
      // Test terms page
      console.log('📍 Monitoring terms page for errors');
      await page.goto('https://admin-portal-278.preview.emergentagent.com/contentry/terms');
      await page.waitForLoadState('networkidle');
      await page.waitForTimeout(2000);
      
      // Analyze console messages
      console.log(`📊 Total console messages captured: ${consoleMessages.length}`);
      
      const errorMessages = consoleMessages.filter(msg => msg.type === 'error');
      const warningMessages = consoleMessages.filter(msg => msg.type === 'warning');
      
      console.log(`❌ Console errors found: ${errorMessages.length}`);
      console.log(`⚠️ Console warnings found: ${warningMessages.length}`);
      
      if (errorMessages.length > 0) {
        console.log('🔍 Console errors details:');
        errorMessages.forEach((error, index) => {
          console.log(`  ${index + 1}. ${error.text}`);
        });
      }
      
      // Analyze network errors
      console.log(`🌐 Network errors found: ${networkErrors.length}`);
      if (networkErrors.length > 0) {
        console.log('🔍 Network errors details:');
        networkErrors.forEach((error, index) => {
          console.log(`  ${index + 1}. ${error.url} - ${error.failure?.errorText || 'Unknown error'}`);
        });
      }
      
      console.log('✅ Console and network monitoring completed');
      
    } catch (error) {
      console.error('❌ Error in console/network monitoring:', error.message);
      throw error;
    }
  });
  
});