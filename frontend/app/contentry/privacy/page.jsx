'use client';
import { useTranslation } from 'react-i18next';
import {
  Box,
  Container,
  Heading,
  Text,
  VStack,
  useColorModeValue,
  List,
  ListItem,
  ListIcon,
  Divider,
} from '@chakra-ui/react';
import { FaShieldAlt } from 'react-icons/fa';

export default function PrivacyPolicyPage() {
  const textColor = useColorModeValue('gray.800', 'white');
  const headingColor = useColorModeValue('brand.600', 'brand.300');
  const bgColor = useColorModeValue('white', 'gray.800');

  return (
    <Box minH="100vh" bg={useColorModeValue('gray.50', 'gray.900')} py={10}>
      <Container maxW="4xl" bg={bgColor} p={8} borderRadius="lg" boxShadow="lg">
        <VStack spacing={6} align="stretch">
          {/* Header */}
          <VStack spacing={2} align="center">
            <FaShieldAlt size={48} color={useColorModeValue('#4299E1', '#63B3ED')} />
            <Heading size="2xl" color={headingColor} textAlign="center">
              Privacy Policy
            </Heading>
            <Text fontSize="sm" color="gray.500" textAlign="center">
              Last Updated: November 29, 2024
            </Text>
          </VStack>

          <Divider />

          {/* Introduction */}
          <Box>
            <Text fontSize="md" color={textColor} lineHeight="tall">
              At Contentry, we take your privacy seriously. This Privacy Policy explains how we collect, use, disclose, and safeguard your information when you use our platform for content analysis and risk assessment.
            </Text>
          </Box>

          {/* Section 1: Information We Collect */}
          <Box>
            <Heading size="md" color={headingColor} mb={3}>
              1. Information We Collect
            </Heading>
            <List spacing={2}>
              <ListItem color={textColor}>
                <ListIcon as={FaShieldAlt} color="brand.500" />
                <strong>Personal Information:</strong> Name, email address, phone number (if provided), and payment information.
              </ListItem>
              <ListItem color={textColor}>
                <ListIcon as={FaShieldAlt} color="brand.500" />
                <strong>Content Data:</strong> Text, images, videos, and other content you submit for analysis.
              </ListItem>
              <ListItem color={textColor}>
                <ListIcon as={FaShieldAlt} color="brand.500" />
                <strong>Usage Data:</strong> Information about how you interact with our platform, including IP address, browser type, device information, and usage patterns.
              </ListItem>
              <ListItem color={textColor}>
                <ListIcon as={FaShieldAlt} color="brand.500" />
                <strong>OAuth Data:</strong> When you log in using third-party OAuth providers (Google, Microsoft, Apple, Slack), we receive your profile information as permitted by those services.
              </ListItem>
            </List>
          </Box>

          {/* Section 2: How We Use Your Information */}
          <Box>
            <Heading size="md" color={headingColor} mb={3}>
              2. How We Use Your Information
            </Heading>
            <List spacing={2}>
              <ListItem color={textColor}>
                <ListIcon as={FaShieldAlt} color="brand.500" />
                To provide and maintain our content analysis services
              </ListItem>
              <ListItem color={textColor}>
                <ListIcon as={FaShieldAlt} color="brand.500" />
                To process your payments and manage subscriptions
              </ListItem>
              <ListItem color={textColor}>
                <ListIcon as={FaShieldAlt} color="brand.500" />
                To analyze content for risk assessment, compliance, and cultural sensitivity
              </ListItem>
              <ListItem color={textColor}>
                <ListIcon as={FaShieldAlt} color="brand.500" />
                To improve our AI models and service quality
              </ListItem>
              <ListItem color={textColor}>
                <ListIcon as={FaShieldAlt} color="brand.500" />
                To communicate with you about your account and services
              </ListItem>
              <ListItem color={textColor}>
                <ListIcon as={FaShieldAlt} color="brand.500" />
                To send you marketing communications (only if you&apos;ve consented)
              </ListItem>
            </List>
          </Box>

          {/* Section 3: GDPR Compliance */}
          <Box>
            <Heading size="md" color={headingColor} mb={3}>
              3. Your Rights Under GDPR
            </Heading>
            <Text fontSize="md" color={textColor} mb={3}>
              If you are a resident of the European Economic Area (EEA), you have the following data protection rights:
            </Text>
            <List spacing={2}>
              <ListItem color={textColor}>
                <ListIcon as={FaShieldAlt} color="brand.500" />
                <strong>Right to Access:</strong> You can request a copy of your personal data.
              </ListItem>
              <ListItem color={textColor}>
                <ListIcon as={FaShieldAlt} color="brand.500" />
                <strong>Right to Rectification:</strong> You can request correction of inaccurate data.
              </ListItem>
              <ListItem color={textColor}>
                <ListIcon as={FaShieldAlt} color="brand.500" />
                <strong>Right to Erasure:</strong> You can request deletion of your personal data.
              </ListItem>
              <ListItem color={textColor}>
                <ListIcon as={FaShieldAlt} color="brand.500" />
                <strong>Right to Restrict Processing:</strong> You can request that we limit how we use your data.
              </ListItem>
              <ListItem color={textColor}>
                <ListIcon as={FaShieldAlt} color="brand.500" />
                <strong>Right to Data Portability:</strong> You can receive your data in a machine-readable format.
              </ListItem>
              <ListItem color={textColor}>
                <ListIcon as={FaShieldAlt} color="brand.500" />
                <strong>Right to Object:</strong> You can object to processing of your data for direct marketing.
              </ListItem>
              <ListItem color={textColor}>
                <ListIcon as={FaShieldAlt} color="brand.500" />
                <strong>Right to Withdraw Consent:</strong> You can withdraw consent at any time where we rely on consent.
              </ListItem>
            </List>
          </Box>

          {/* Section 4: Data Retention */}
          <Box>
            <Heading size="md" color={headingColor} mb={3}>
              4. Data Retention
            </Heading>
            <Text fontSize="md" color={textColor}>
              We retain your personal data only for as long as necessary to fulfill the purposes outlined in this Privacy Policy, unless a longer retention period is required by law. Content submitted for analysis is retained for 90 days unless you request earlier deletion.
            </Text>
          </Box>

          {/* Section 5: Data Security */}
          <Box>
            <Heading size="md" color={headingColor} mb={3}>
              5. Data Security
            </Heading>
            <Text fontSize="md" color={textColor}>
              We implement appropriate technical and organizational security measures to protect your personal data against unauthorized access, alteration, disclosure, or destruction. This includes encryption, access controls, and regular security audits.
            </Text>
          </Box>

          {/* Section 6: Third-Party Services */}
          <Box>
            <Heading size="md" color={headingColor} mb={3}>
              6. Third-Party Services
            </Heading>
            <Text fontSize="md" color={textColor} mb={2}>
              We use the following third-party services:
            </Text>
            <List spacing={2}>
              <ListItem color={textColor}>
                <ListIcon as={FaShieldAlt} color="brand.500" />
                <strong>Stripe:</strong> For payment processing (see Stripe&apos;s Privacy Policy)
              </ListItem>
              <ListItem color={textColor}>
                <ListIcon as={FaShieldAlt} color="brand.500" />
                <strong>OAuth Providers:</strong> Google, Microsoft, Apple, Slack for authentication
              </ListItem>
              <ListItem color={textColor}>
                <ListIcon as={FaShieldAlt} color="brand.500" />
                <strong>AI Services:</strong> OpenAI, Google AI for content analysis
              </ListItem>
            </List>
          </Box>

          {/* Section 7: Cookies */}
          <Box>
            <Heading size="md" color={headingColor} mb={3}>
              7. Cookies and Tracking
            </Heading>
            <Text fontSize="md" color={textColor}>
              We use cookies and similar tracking technologies to track activity on our platform and store certain information. You can instruct your browser to refuse all cookies or to indicate when a cookie is being sent.
            </Text>
          </Box>

          {/* Section 8: International Data Transfers */}
          <Box>
            <Heading size="md" color={headingColor} mb={3}>
              8. International Data Transfers
            </Heading>
            <Text fontSize="md" color={textColor}>
              Your information may be transferred to and maintained on servers located outside of your country. We ensure that appropriate safeguards are in place to protect your data in accordance with this Privacy Policy.
            </Text>
          </Box>

          {/* Section 9: Changes to This Policy */}
          <Box>
            <Heading size="md" color={headingColor} mb={3}>
              9. Changes to This Privacy Policy
            </Heading>
            <Text fontSize="md" color={textColor}>
              We may update this Privacy Policy from time to time. We will notify you of any changes by posting the new Privacy Policy on this page and updating the &quot;Last Updated&quot; date. You are advised to review this Privacy Policy periodically.
            </Text>
          </Box>

          {/* Contact Information */}
          <Box bg={useColorModeValue('blue.50', 'gray.700')} p={4} borderRadius="md">
            <Heading size="sm" color={headingColor} mb={2}>
              Contact Us
            </Heading>
            <Text fontSize="md" color={textColor}>
              If you have any questions about this Privacy Policy or wish to exercise your GDPR rights, please contact us at:
            </Text>
            <Text fontSize="md" color={textColor} mt={2}>
              <strong>Email:</strong> privacy@contentry.com<br />
              <strong>Address:</strong> [Your Company Address]
            </Text>
          </Box>
        </VStack>
      </Container>
    </Box>
  );
}
