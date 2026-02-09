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
  Link,
} from '@chakra-ui/react';
import { FaFileContract } from 'react-icons/fa';

export default function TermsOfServicePage() {
  const textColor = useColorModeValue('gray.800', 'white');
  const headingColor = useColorModeValue('brand.600', 'brand.300');
  const bgColor = useColorModeValue('white', 'gray.800');

  return (
    <Box minH="100vh" bg={useColorModeValue('gray.50', 'gray.900')} py={10}>
      <Container maxW="4xl" bg={bgColor} p={8} borderRadius="lg" boxShadow="lg">
        <VStack spacing={6} align="stretch">
          {/* Header */}
          <VStack spacing={2} align="center">
            <FaFileContract size={48} color={useColorModeValue('#4299E1', '#63B3ED')} />
            <Heading size="2xl" color={headingColor} textAlign="center">
              Terms of Service
            </Heading>
            <Text fontSize="sm" color="gray.500" textAlign="center">
              Last Updated: November 29, 2024
            </Text>
          </VStack>

          <Divider />

          {/* Introduction */}
          <Box>
            <Text fontSize="md" color={textColor} lineHeight="tall">
              Welcome to Contentry. By accessing or using our platform, you agree to be bound by these Terms of Service (&quot;Terms&quot;). Please read them carefully before using our services.
            </Text>
          </Box>

          {/* Section 1: Acceptance of Terms */}
          <Box>
            <Heading size="md" color={headingColor} mb={3}>
              1. Acceptance of Terms
            </Heading>
            <Text fontSize="md" color={textColor}>
              By creating an account, accessing, or using Contentry&apos;s services, you acknowledge that you have read, understood, and agree to be bound by these Terms and our Privacy Policy. If you do not agree, please do not use our services.
            </Text>
          </Box>

          {/* Section 2: Description of Service */}
          <Box>
            <Heading size="md" color={headingColor} mb={3}>
              2. Description of Service
            </Heading>
            <Text fontSize="md" color={textColor} mb={2}>
              Contentry provides AI-powered content analysis and risk assessment services, including:
            </Text>
            <List spacing={2}>
              <ListItem color={textColor}>
                <ListIcon as={FaFileContract} color="brand.500" />
                Content moderation and compliance analysis
              </ListItem>
              <ListItem color={textColor}>
                <ListIcon as={FaFileContract} color="brand.500" />
                Cultural sensitivity assessment
              </ListItem>
              <ListItem color={textColor}>
                <ListIcon as={FaFileContract} color="brand.500" />
                Content generation and scheduling
              </ListItem>
              <ListItem color={textColor}>
                <ListIcon as={FaFileContract} color="brand.500" />
                Social media history analysis for organizational risk assessment
              </ListItem>
              <ListItem color={textColor}>
                <ListIcon as={FaFileContract} color="brand.500" />
                Analytics and reporting dashboards
              </ListItem>
            </List>
          </Box>

          {/* Section 3: User Accounts */}
          <Box>
            <Heading size="md" color={headingColor} mb={3}>
              3. User Accounts and Registration
            </Heading>
            <List spacing={2}>
              <ListItem color={textColor}>
                <ListIcon as={FaFileContract} color="brand.500" />
                You are responsible for maintaining the confidentiality of your account credentials.
              </ListItem>
              <ListItem color={textColor}>
                <ListIcon as={FaFileContract} color="brand.500" />
                You agree to provide accurate and complete information during registration.
              </ListItem>
              <ListItem color={textColor}>
                <ListIcon as={FaFileContract} color="brand.500" />
                You are responsible for all activities that occur under your account.
              </ListItem>
              <ListItem color={textColor}>
                <ListIcon as={FaFileContract} color="brand.500" />
                You must notify us immediately of any unauthorized use of your account.
              </ListItem>
            </List>
          </Box>

          {/* Section 4: Subscription and Payment */}
          <Box>
            <Heading size="md" color={headingColor} mb={3}>
              4. Subscription and Payment
            </Heading>
            <Text fontSize="md" color={textColor} mb={2}>
              Access to Contentry requires an active subscription:
            </Text>
            <List spacing={2}>
              <ListItem color={textColor}>
                <ListIcon as={FaFileContract} color="brand.500" />
                Subscriptions are billed on a recurring basis (monthly or annually).
              </ListItem>
              <ListItem color={textColor}>
                <ListIcon as={FaFileContract} color="brand.500" />
                Payment processing is handled by Stripe, our third-party payment processor.
              </ListItem>
              <ListItem color={textColor}>
                <ListIcon as={FaFileContract} color="brand.500" />
                You authorize us to charge your payment method for all subscription fees.
              </ListItem>
              <ListItem color={textColor}>
                <ListIcon as={FaFileContract} color="brand.500" />
                Subscription fees are non-refundable except as required by law.
              </ListItem>
              <ListItem color={textColor}>
                <ListIcon as={FaFileContract} color="brand.500" />
                We reserve the right to change subscription pricing with 30 days&apos; notice.
              </ListItem>
              <ListItem color={textColor}>
                <ListIcon as={FaFileContract} color="brand.500" />
                Failure to maintain an active subscription will result in loss of access to the platform.
              </ListItem>
            </List>
          </Box>

          {/* Section 5: Acceptable Use */}
          <Box>
            <Heading size="md" color={headingColor} mb={3}>
              5. Acceptable Use Policy
            </Heading>
            <Text fontSize="md" color={textColor} mb={2}>
              You agree not to:
            </Text>
            <List spacing={2}>
              <ListItem color={textColor}>
                <ListIcon as={FaFileContract} color="brand.500" />
                Use the service for any illegal or unauthorized purpose.
              </ListItem>
              <ListItem color={textColor}>
                <ListIcon as={FaFileContract} color="brand.500" />
                Violate any laws in your jurisdiction (including copyright laws).
              </ListItem>
              <ListItem color={textColor}>
                <ListIcon as={FaFileContract} color="brand.500" />
                Upload content containing malware, viruses, or harmful code.
              </ListItem>
              <ListItem color={textColor}>
                <ListIcon as={FaFileContract} color="brand.500" />
                Attempt to gain unauthorized access to our systems or other users&apos; accounts.
              </ListItem>
              <ListItem color={textColor}>
                <ListIcon as={FaFileContract} color="brand.500" />
                Use automated systems (bots, scrapers) to access the service without permission.
              </ListItem>
              <ListItem color={textColor}>
                <ListIcon as={FaFileContract} color="brand.500" />
                Reverse engineer, decompile, or disassemble any part of the service.
              </ListItem>
              <ListItem color={textColor}>
                <ListIcon as={FaFileContract} color="brand.500" />
                Resell or redistribute the service without our written permission.
              </ListItem>
            </List>
          </Box>

          {/* Section 6: Content Ownership */}
          <Box>
            <Heading size="md" color={headingColor} mb={3}>
              6. Content Ownership and License
            </Heading>
            <Text fontSize="md" color={textColor} mb={2}>
              <strong>Your Content:</strong> You retain all ownership rights to content you submit to Contentry. By uploading content, you grant us a limited license to process, analyze, and store your content solely for the purpose of providing our services.
            </Text>
            <Text fontSize="md" color={textColor} mb={2}>
              <strong>Our Content:</strong> All intellectual property rights in the Contentry platform, including software, algorithms, and documentation, are owned by us or our licensors.
            </Text>
            <Text fontSize="md" color={textColor}>
              <strong>AI-Generated Content:</strong> Content generated by our AI tools is provided to you under a royalty-free license for your use.
            </Text>
          </Box>

          {/* Section 7: Limitation of Liability */}
          <Box>
            <Heading size="md" color={headingColor} mb={3}>
              7. Limitation of Liability
            </Heading>
            <Text fontSize="md" color={textColor} mb={2}>
              To the maximum extent permitted by law:
            </Text>
            <List spacing={2}>
              <ListItem color={textColor}>
                <ListIcon as={FaFileContract} color="brand.500" />
                Contentry is provided &quot;as is&quot; without warranties of any kind.
              </ListItem>
              <ListItem color={textColor}>
                <ListIcon as={FaFileContract} color="brand.500" />
                We do not guarantee that the service will be uninterrupted or error-free.
              </ListItem>
              <ListItem color={textColor}>
                <ListIcon as={FaFileContract} color="brand.500" />
                We are not liable for any indirect, incidental, or consequential damages.
              </ListItem>
              <ListItem color={textColor}>
                <ListIcon as={FaFileContract} color="brand.500" />
                Our total liability is limited to the amount you paid in the last 12 months.
              </ListItem>
              <ListItem color={textColor}>
                <ListIcon as={FaFileContract} color="brand.500" />
                AI analysis results are advisory only; you are responsible for final decisions.
              </ListItem>
            </List>
          </Box>

          {/* Section 8: Data Privacy */}
          <Box>
            <Heading size="md" color={headingColor} mb={3}>
              8. Data Privacy and Security
            </Heading>
            <Text fontSize="md" color={textColor}>
              Your use of Contentry is also governed by our Privacy Policy, which explains how we collect, use, and protect your data. We implement industry-standard security measures, but cannot guarantee absolute security.
            </Text>
          </Box>

          {/* Section 9: Termination */}
          <Box>
            <Heading size="md" color={headingColor} mb={3}>
              9. Termination
            </Heading>
            <Text fontSize="md" color={textColor} mb={2}>
              We reserve the right to:
            </Text>
            <List spacing={2}>
              <ListItem color={textColor}>
                <ListIcon as={FaFileContract} color="brand.500" />
                Suspend or terminate your account for violation of these Terms.
              </ListItem>
              <ListItem color={textColor}>
                <ListIcon as={FaFileContract} color="brand.500" />
                Refuse service to anyone for any reason at any time.
              </ListItem>
              <ListItem color={textColor}>
                <ListIcon as={FaFileContract} color="brand.500" />
                Terminate accounts with expired or invalid subscriptions.
              </ListItem>
            </List>
            <Text fontSize="md" color={textColor} mt={2}>
              You may cancel your subscription at any time through your account settings.
            </Text>
          </Box>

          {/* Section 10: Indemnification */}
          <Box>
            <Heading size="md" color={headingColor} mb={3}>
              10. Indemnification
            </Heading>
            <Text fontSize="md" color={textColor}>
              You agree to indemnify and hold harmless Contentry and its officers, directors, employees, and agents from any claims, damages, losses, liabilities, and expenses (including legal fees) arising from your use of the service or violation of these Terms.
            </Text>
          </Box>

          {/* Section 11: Changes to Terms */}
          <Box>
            <Heading size="md" color={headingColor} mb={3}>
              11. Changes to Terms
            </Heading>
            <Text fontSize="md" color={textColor}>
              We reserve the right to modify these Terms at any time. We will notify you of material changes by email or through the platform. Your continued use of the service after changes constitutes acceptance of the modified Terms.
            </Text>
          </Box>

          {/* Section 12: Governing Law */}
          <Box>
            <Heading size="md" color={headingColor} mb={3}>
              12. Governing Law and Dispute Resolution
            </Heading>
            <Text fontSize="md" color={textColor} mb={2}>
              These Terms are governed by the laws of Norway. Any disputes will be resolved by the courts of Oslo, Norway.
            </Text>
            <Text fontSize="md" color={textColor} mb={2}>
              <strong>EU Consumer Rights:</strong> If you are an EU consumer, you may have additional rights under EU consumer protection laws that cannot be waived by contract.
            </Text>
            <Text fontSize="md" color={textColor}>
              <strong>EU Online Dispute Resolution:</strong> For users in the European Union, you may refer disputes to the European Commission&apos;s Online Dispute Resolution platform at{' '}
              <Link href="https://ec.europa.eu/consumers/odr/" isExternal color="brand.500">
                https://ec.europa.eu/consumers/odr/
              </Link>
            </Text>
          </Box>

          {/* Contact Information */}
          <Box bg={useColorModeValue('blue.50', 'gray.700')} p={4} borderRadius="md">
            <Heading size="sm" color={headingColor} mb={2}>
              Contact Us
            </Heading>
            <Text fontSize="md" color={textColor}>
              If you have any questions about these Terms of Service, please contact us at:
            </Text>
            <Text fontSize="md" color={textColor} mt={2}>
              <strong>Global InTech AS</strong><br />
              Røo 95, 5457 Høylandsbygd, Norway<br />
              Organization Number: NO 935 706 998<br />
              <strong>Email:</strong> legal@contentry.ai
            </Text>
          </Box>
        </VStack>
      </Container>
    </Box>
  );
}
