'use client';
import { useTranslation } from 'react-i18next';
import { useState, useEffect } from 'react';
import {
  Box, Button, Card, CardBody, Flex, FormControl, FormLabel, Input, Select,
  Text, VStack, useColorModeValue, Heading, Icon, Avatar, useToast,
  Modal, ModalOverlay, ModalContent, ModalHeader, ModalBody, ModalCloseButton,
  ModalFooter, useDisclosure, Table, Thead, Tbody, Tr, Th, Td, Badge, Divider,
  Alert, AlertIcon, AlertTitle, AlertDescription, HStack, Tabs, TabList, TabPanels, Tab, TabPanel
} from '@chakra-ui/react';
import { FaBuilding, FaArrowLeft, FaUpload, FaTrash, FaFileAlt, FaShieldAlt, FaBriefcase, FaGlobe, FaInfoCircle } from 'react-icons/fa';
import { useRouter } from 'next/navigation';
import axios from 'axios';
import { getApiUrl } from '@/lib/api';

// Categories for Universal Company Policies
const UNIVERSAL_POLICY_CATEGORIES = [
  { value: 'code_of_conduct', label: 'Code of Conduct' },
  { value: 'social_media_policy', label: 'Social Media Policy' },
  { value: 'acceptable_use', label: 'Acceptable Use Policy' },
  { value: 'harassment_workplace', label: 'Harassment & Workplace Respect Policy' },
  { value: 'data_protection', label: 'Data Protection & Privacy Policy (GDPR/CCPA)' },
  { value: 'confidentiality', label: 'Confidentiality Agreement (NDA)' },
  { value: 'safety_security', label: 'Safety & Security Policy' },
  { value: 'whistleblowing_ethics', label: 'Whistleblowing & Ethics Reporting Policy' },
  { value: 'other', label: 'Other' }
];

// Categories for Professional Brand & Compliance
const PROFESSIONAL_BRAND_CATEGORIES = [
  { value: 'brand_guidelines', label: 'Brand Guidelines' },
  { value: 'tone_of_voice', label: 'Tone of Voice Guide' },
  { value: 'visual_identity', label: 'Visual Identity Standards' },
  { value: 'product_messaging', label: 'Product Messaging Guide' },
  { value: 'marketing_compliance', label: 'Marketing Compliance' },
  { value: 'media_communication', label: 'Media Communication / PR Policy' },
  { value: 'customer_communication', label: 'Customer Communication Standards' },
  { value: 'industry_compliance', label: 'Industry-Specific Compliance' },
  { value: 'other', label: 'Other' }
];

// DocumentsTable component - moved outside to avoid nested component issue
function DocumentsTable({ documents, tier, emptyMessage, textColorSecondary, onUpload, onDelete }) {
  if (documents.length === 0) {
    return (
      <Box textAlign="center" py={8}>
        <Icon as={FaFileAlt} boxSize={12} color={textColorSecondary} mb={4} />
        <Text color={textColorSecondary} mb={4}>{emptyMessage}</Text>
        <Button
          leftIcon={<Icon as={FaUpload} />}
          colorScheme={tier === 'universal' ? 'red' : 'blue'}
          onClick={() => onUpload(tier)}
        >
          Upload Document
        </Button>
      </Box>
    );
  }

  return (
    <Box overflowX="auto">
      <Table variant="simple" size="sm">
        <Thead>
          <Tr>
            <Th>Document Name</Th>
            <Th>Type</Th>
            <Th>Size</Th>
            <Th>Chunks</Th>
            <Th>Uploaded</Th>
            <Th>Actions</Th>
          </Tr>
        </Thead>
        <Tbody>
          {documents.map((doc) => (
            <Tr key={doc.id}>
              <Td fontWeight="600" maxW="200px" isTruncated>{doc.filename}</Td>
              <Td>{doc.file_type || 'N/A'}</Td>
              <Td>{doc.file_size ? `${(doc.file_size / 1024).toFixed(1)} KB` : 'N/A'}</Td>
              <Td>
                <Badge colorScheme={tier === 'universal' ? 'red' : 'blue'}>
                  {doc.chunk_count || 0} chunks
                </Badge>
              </Td>
              <Td>{doc.created_at ? new Date(doc.created_at).toLocaleDateString() : 'N/A'}</Td>
              <Td>
                <Button
                  size="xs"
                  colorScheme="red"
                  variant="ghost"
                  leftIcon={<Icon as={FaTrash} />}
                  onClick={() => onDelete(doc.id, tier)}
                >
                  Delete
                </Button>
              </Td>
            </Tr>
          ))}
        </Tbody>
      </Table>
    </Box>
  );
}

export default function CompanyProfilePage() {
  const { t } = useTranslation();
  const [user, setUser] = useState(null);
  const [companyData, setCompanyData] = useState({
    name: '',
    company_logo: null,
    website: '',
    address: '',
    city: '',
    state: '',
    country: '',
    postal_code: '',
    phone: '',
    linkedin_url: '',
    twitter_url: '',
    facebook_url: '',
    instagram_url: ''
  });
  
  // Two separate document lists for the two tiers
  const [universalDocuments, setUniversalDocuments] = useState([]);
  const [professionalDocuments, setProfessionalDocuments] = useState([]);
  const [knowledgeStats, setKnowledgeStats] = useState({ universal: {}, professional: {} });
  
  const [loading, setLoading] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [selectedFile, setSelectedFile] = useState(null);
  const [selectedCategory, setSelectedCategory] = useState('other');
  const [uploadTier, setUploadTier] = useState('universal'); // 'universal' or 'professional'
  
  const router = useRouter();
  const toast = useToast();
  const { isOpen, onOpen, onClose } = useDisclosure();
  
  const bgColor = useColorModeValue('white', 'gray.800');
  const textColor = useColorModeValue('gray.800', 'white');
  const textColorSecondary = useColorModeValue('gray.600', 'gray.400');
  const selectedFileBg = useColorModeValue('blue.50', 'blue.900');
  const universalBg = useColorModeValue('red.50', 'red.900');
  const professionalBg = useColorModeValue('blue.50', 'blue.900');

  useEffect(() => {
    const storedUser = localStorage.getItem('contentry_user');
    if (storedUser) {
      const userData = JSON.parse(storedUser);
      setUser(userData);
      
      // Check if user is enterprise admin (accept both 'admin' and 'enterprise_admin' roles)
      const isEnterpriseAdmin = userData.enterprise_role === 'enterprise_admin' || 
                                 userData.enterprise_role === 'admin' ||
                                 userData.is_enterprise_admin === true;
      
      if (!isEnterpriseAdmin || !userData.enterprise_id) {
        router.push('/contentry/dashboard');
        return;
      }
      
      loadCompanyData(userData.enterprise_id, userData.id);
      loadAllDocuments(userData.id);
      loadKnowledgeStats(userData.id);
    } else {
      router.push('/contentry/auth/login');
    }
  }, [router]);

  const loadCompanyData = async (enterpriseId, userId) => {
    try {
      const API = getApiUrl();
      const response = await axios.get(`${API}/enterprises/${enterpriseId}/settings/company`, {
        headers: { 'X-User-ID': userId }
      });
      setCompanyData({
        name: response.data.name || '',
        company_logo: response.data.company_logo || null,
        website: response.data.website || '',
        address: response.data.address || '',
        city: response.data.city || '',
        state: response.data.state || '',
        country: response.data.country || '',
        postal_code: response.data.postal_code || '',
        phone: response.data.phone || '',
        linkedin_url: response.data.linkedin_url || '',
        twitter_url: response.data.twitter_url || '',
        facebook_url: response.data.facebook_url || '',
        instagram_url: response.data.instagram_url || ''
      });
    } catch (error) {
      console.error('Failed to load company data:', error);
    }
  };

  const loadAllDocuments = async (userId) => {
    const API = getApiUrl();
    
    // Load Universal documents
    try {
      const universalResponse = await axios.get(
        `${API}/company/knowledge/universal/documents`,
        { headers: { 'X-User-ID': userId } }
      );
      setUniversalDocuments(universalResponse.data.documents || []);
    } catch (error) {
      console.error('Failed to load universal documents:', error);
    }
    
    // Load Professional documents
    try {
      const professionalResponse = await axios.get(
        `${API}/company/knowledge/professional/documents`,
        { headers: { 'X-User-ID': userId } }
      );
      setProfessionalDocuments(professionalResponse.data.documents || []);
    } catch (error) {
      console.error('Failed to load professional documents:', error);
    }
  };

  const loadKnowledgeStats = async (userId) => {
    try {
      const API = getApiUrl();
      const response = await axios.get(
        `${API}/company/knowledge/stats`,
        { headers: { 'X-User-ID': userId } }
      );
      setKnowledgeStats(response.data);
    } catch (error) {
      console.error('Failed to load knowledge stats:', error);
    }
  };

  const handleLogoUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;
    
    if (!file.type.startsWith('image/')) {
      toast({
        title: 'Invalid file type',
        description: 'Please select an image file',
        status: 'error',
        duration: 3000
      });
      return;
    }

    try {
      const API = getApiUrl();
      const formData = new FormData();
      formData.append('file', file);
      formData.append('user_id', user.id);

      const uploadResponse = await axios.post(`${API}/auth/upload-avatar`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
          'X-User-ID': user.id
        }
      });

      const logoUrl = uploadResponse.data.avatar_url;

      await axios.post(
        `${API}/enterprises/${user.enterprise_id}/settings/upload-logo`,
        { logo_url: logoUrl },
        { headers: { 'X-User-ID': user.id } }
      );

      setCompanyData({ ...companyData, company_logo: logoUrl });
      
      toast({
        title: 'Company logo uploaded successfully!',
        status: 'success',
        duration: 3000
      });
    } catch (error) {
      console.error('Error uploading logo:', error);
      toast({
        title: 'Failed to upload logo',
        description: error.response?.data?.detail || error.message,
        status: 'error',
        duration: 5000
      });
    }
  };

  const handleSave = async () => {
    setLoading(true);
    try {
      const API = getApiUrl();
      await axios.put(
        `${API}/enterprises/${user.enterprise_id}/settings/company`,
        { 
          name: companyData.name,
          website: companyData.website,
          address: companyData.address,
          city: companyData.city,
          state: companyData.state,
          country: companyData.country,
          postal_code: companyData.postal_code,
          phone: companyData.phone,
          linkedin_url: companyData.linkedin_url,
          twitter_url: companyData.twitter_url,
          facebook_url: companyData.facebook_url,
          instagram_url: companyData.instagram_url
        },
        { headers: { 'X-User-ID': user.id } }
      );
      
      toast({
        title: 'Company profile updated successfully!',
        status: 'success',
        duration: 3000
      });
    } catch (error) {
      console.error('Error updating company:', error);
      toast({
        title: 'Failed to update company profile',
        description: error.response?.data?.detail || error.message,
        status: 'error',
        duration: 5000
      });
    } finally {
      setLoading(false);
    }
  };

  const handleFileSelect = (e) => {
    setSelectedFile(e.target.files[0]);
  };

  const openUploadModal = (tier) => {
    setUploadTier(tier);
    setSelectedCategory('other');
    setSelectedFile(null);
    onOpen();
  };

  const handleUploadDocument = async () => {
    if (!selectedFile) {
      toast({
        title: 'No file selected',
        status: 'warning',
        duration: 3000
      });
      return;
    }

    setUploading(true);
    try {
      const API = getApiUrl();
      const formData = new FormData();
      formData.append('file', selectedFile);

      const endpoint = uploadTier === 'universal' 
        ? `${API}/company/knowledge/universal/upload`
        : `${API}/company/knowledge/professional/upload`;

      await axios.post(endpoint, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
          'X-User-ID': user.id
        }
      });

      const tierLabel = uploadTier === 'universal' ? 'Universal Policy' : 'Professional Brand';
      toast({
        title: `${tierLabel} document uploaded successfully!`,
        status: 'success',
        duration: 3000
      });

      loadAllDocuments(user.id);
      loadKnowledgeStats(user.id);
      onClose();
      setSelectedFile(null);
      setSelectedCategory('other');
    } catch (error) {
      console.error('Error uploading document:', error);
      toast({
        title: 'Failed to upload document',
        description: error.response?.data?.detail || error.message,
        status: 'error',
        duration: 5000
      });
    } finally {
      setUploading(false);
    }
  };

  const handleDeleteDocument = async (docId, tier) => {
    if (!confirm('Are you sure you want to delete this document?')) return;

    try {
      const API = getApiUrl();
      const endpoint = tier === 'universal'
        ? `${API}/company/knowledge/universal/documents/${docId}`
        : `${API}/company/knowledge/professional/documents/${docId}`;
        
      await axios.delete(endpoint, {
        headers: { 'X-User-ID': user.id }
      });

      toast({
        title: 'Document deleted successfully',
        status: 'success',
        duration: 3000
      });

      loadAllDocuments(user.id);
      loadKnowledgeStats(user.id);
    } catch (error) {
      console.error('Error deleting document:', error);
      toast({
        title: 'Failed to delete document',
        description: error.response?.data?.detail || error.message,
        status: 'error',
        duration: 5000
      });
    }
  };

  const getCategoryLabel = (value, tier) => {
    const categories = tier === 'universal' ? UNIVERSAL_POLICY_CATEGORIES : PROFESSIONAL_BRAND_CATEGORIES;
    const category = categories.find(c => c.value === value);
    return category ? category.label : value;
  };

  if (!user) return null;

  const getLogoUrl = (url) => {
    if (!url) return null;
    if (url.startsWith('blob:')) return url;
    if (url.startsWith('http')) return url;
    return `${process.env.NEXT_PUBLIC_BACKEND_URL || ''}${url}`;
  };

  return (
    <Box pt={{ base: '130px', md: '80px', xl: '80px' }}>
      <Button
        leftIcon={<Icon as={FaArrowLeft} />}
        variant="ghost"
        mb={4}
        onClick={() => router.push('/contentry/enterprise/settings')}
      >
        Back to Company Settings
      </Button>

      <VStack spacing={6} align="stretch">
        {/* Company Profile Section */}
        <Card bg={bgColor} boxShadow="lg">
          <CardBody p={{ base: 4, md: 6 }}>
            <Flex align="center" gap={3} mb={6}>
              <Icon as={FaBuilding} boxSize={6} color="brand.500" />
              <Heading size="lg" color={textColor}>Company Profile</Heading>
            </Flex>

            <VStack spacing={6} align="stretch">
              {/* Company Logo */}
              <FormControl>
                <FormLabel fontWeight="600">Company Logo</FormLabel>
                <Flex align="center" gap={4}>
                  <Avatar
                    size="xl"
                    src={getLogoUrl(companyData.company_logo)}
                    name={companyData.name}
                    icon={<Icon as={FaBuilding} boxSize={10} />}
                    bg="brand.500"
                    color="white"
                  />
                  <Box>
                    <Input
                      type="file"
                      accept="image/*"
                      onChange={handleLogoUpload}
                      display="none"
                      id="logo-upload"
                    />
                    <Button
                      as="label"
                      htmlFor="logo-upload"
                      size="sm"
                      colorScheme="brand"
                      cursor="pointer"
                    >
                      Upload Logo
                    </Button>
                    <Text fontSize="xs" color={textColorSecondary} mt={2}>
                      Recommended: Square image, 512x512px or larger
                    </Text>
                  </Box>
                </Flex>
              </FormControl>

              {/* Company Name */}
              <FormControl>
                <FormLabel fontWeight="600">Company Name</FormLabel>
                <Input
                  value={companyData.name}
                  onChange={(e) => setCompanyData({ ...companyData, name: e.target.value })}
                  placeholder="Enter company name"
                />
              </FormControl>

              {/* Website */}
              <FormControl>
                <FormLabel fontWeight="600">
                  <HStack>
                    <Icon as={FaGlobe} />
                    <Text>Website</Text>
                  </HStack>
                </FormLabel>
                <Input
                  value={companyData.website}
                  onChange={(e) => setCompanyData({ ...companyData, website: e.target.value })}
                  placeholder="https://www.yourcompany.com"
                  type="url"
                />
              </FormControl>

              <Divider />

              {/* Address Section */}
              <Box>
                <Heading size="sm" mb={4} color={textColor}>Company Address</Heading>
                <VStack spacing={4}>
                  <FormControl>
                    <FormLabel fontWeight="600">Street Address</FormLabel>
                    <Input
                      value={companyData.address}
                      onChange={(e) => setCompanyData({ ...companyData, address: e.target.value })}
                      placeholder="123 Main Street, Suite 100"
                    />
                  </FormControl>

                  <HStack spacing={4} w="full">
                    <FormControl>
                      <FormLabel fontWeight="600">City</FormLabel>
                      <Input
                        value={companyData.city}
                        onChange={(e) => setCompanyData({ ...companyData, city: e.target.value })}
                        placeholder="San Francisco"
                      />
                    </FormControl>
                    <FormControl>
                      <FormLabel fontWeight="600">State/Province</FormLabel>
                      <Input
                        value={companyData.state}
                        onChange={(e) => setCompanyData({ ...companyData, state: e.target.value })}
                        placeholder="California"
                      />
                    </FormControl>
                  </HStack>

                  <HStack spacing={4} w="full">
                    <FormControl>
                      <FormLabel fontWeight="600">Postal Code</FormLabel>
                      <Input
                        value={companyData.postal_code}
                        onChange={(e) => setCompanyData({ ...companyData, postal_code: e.target.value })}
                        placeholder="94105"
                      />
                    </FormControl>
                    <FormControl>
                      <FormLabel fontWeight="600">Country</FormLabel>
                      <Input
                        value={companyData.country}
                        onChange={(e) => setCompanyData({ ...companyData, country: e.target.value })}
                        placeholder="United States"
                      />
                    </FormControl>
                  </HStack>

                  <FormControl>
                    <FormLabel fontWeight="600">Phone</FormLabel>
                    <Input
                      value={companyData.phone}
                      onChange={(e) => setCompanyData({ ...companyData, phone: e.target.value })}
                      placeholder="+1 (555) 123-4567"
                      type="tel"
                    />
                  </FormControl>
                </VStack>
              </Box>

              <Divider />

              {/* Social Profiles Section */}
              <Box>
                <Heading size="sm" mb={4} color={textColor}>Company Social Profiles</Heading>
                <VStack spacing={4}>
                  <FormControl>
                    <FormLabel fontWeight="600">
                      <HStack>
                        <Icon as={FaInfoCircle} color="blue.500" />
                        <Text>LinkedIn Company Page</Text>
                      </HStack>
                    </FormLabel>
                    <Input
                      value={companyData.linkedin_url}
                      onChange={(e) => setCompanyData({ ...companyData, linkedin_url: e.target.value })}
                      placeholder="https://www.linkedin.com/company/yourcompany"
                      type="url"
                    />
                  </FormControl>

                  <FormControl>
                    <FormLabel fontWeight="600">
                      <HStack>
                        <Icon as={FaInfoCircle} color="blue.400" />
                        <Text>Twitter/X Profile</Text>
                      </HStack>
                    </FormLabel>
                    <Input
                      value={companyData.twitter_url}
                      onChange={(e) => setCompanyData({ ...companyData, twitter_url: e.target.value })}
                      placeholder="https://twitter.com/yourcompany"
                      type="url"
                    />
                  </FormControl>

                  <FormControl>
                    <FormLabel fontWeight="600">
                      <HStack>
                        <Icon as={FaInfoCircle} color="blue.600" />
                        <Text>Facebook Page</Text>
                      </HStack>
                    </FormLabel>
                    <Input
                      value={companyData.facebook_url}
                      onChange={(e) => setCompanyData({ ...companyData, facebook_url: e.target.value })}
                      placeholder="https://www.facebook.com/yourcompany"
                      type="url"
                    />
                  </FormControl>

                  <FormControl>
                    <FormLabel fontWeight="600">
                      <HStack>
                        <Icon as={FaInfoCircle} color="pink.500" />
                        <Text>Instagram Profile</Text>
                      </HStack>
                    </FormLabel>
                    <Input
                      value={companyData.instagram_url}
                      onChange={(e) => setCompanyData({ ...companyData, instagram_url: e.target.value })}
                      placeholder="https://www.instagram.com/yourcompany"
                      type="url"
                    />
                  </FormControl>
                </VStack>
              </Box>

              {/* Save Button */}
              <Flex justify="flex-end" gap={3}>
                <Button
                  colorScheme="brand"
                  onClick={handleSave}
                  isLoading={loading}
                >
                  Save Changes
                </Button>
              </Flex>
            </VStack>
          </CardBody>
        </Card>

        <Divider />

        {/* Information Alert about the Two-Tier System */}
        <Alert status="info" borderRadius="md" flexDirection="column" alignItems="flex-start" p={4}>
          <Flex align="center" mb={2}>
            <AlertIcon />
            <AlertTitle>Two-Tier Company Knowledge Base System</AlertTitle>
          </Flex>
          <AlertDescription fontSize="sm">
            <Text mb={2}>
              Your company knowledge base is split into two categories for maximum flexibility and compliance:
            </Text>
            <VStack align="start" spacing={1} pl={4}>
              <HStack>
                <Badge colorScheme="red">🔴 Universal Policies</Badge>
                <Text fontSize="sm">Apply to <strong>ALL posts</strong> (Personal & Company/Brand)</Text>
              </HStack>
              <HStack>
                <Badge colorScheme="blue">🟣 Professional Brand</Badge>
                <Text fontSize="sm">Apply only to <strong>Company/Brand posts</strong></Text>
              </HStack>
            </VStack>
            <Text mt={2} fontSize="xs" color={textColorSecondary}>
              This ensures your company is always protected while giving employees creative freedom on personal posts.
            </Text>
          </AlertDescription>
        </Alert>

        {/* Universal Company Policies Section */}
        <Card bg={bgColor} boxShadow="lg" borderLeft="4px solid" borderColor="red.500">
          <CardBody p={{ base: 4, md: 6 }}>
            <Flex align="center" justify="space-between" mb={4}>
              <Flex align="center" gap={3}>
                <Box p={2} bg={universalBg} borderRadius="md">
                  <Icon as={FaShieldAlt} boxSize={6} color="red.500" />
                </Box>
                <Box>
                  <HStack>
                    <Heading size="md" color={textColor}>🔴 Universal Company Policies</Heading>
                    <Badge colorScheme="red" fontSize="sm">{universalDocuments.length} documents</Badge>
                  </HStack>
                  <Text fontSize="sm" color="red.500" fontWeight="600">
                    Applies to ALL Posts (Personal & Company/Brand)
                  </Text>
                </Box>
              </Flex>
              <Button
                leftIcon={<Icon as={FaUpload} />}
                colorScheme="red"
                onClick={() => openUploadModal('universal')}
                size="sm"
              >
                Upload Policy
              </Button>
            </Flex>

            <Alert status="warning" mb={4} borderRadius="md" size="sm">
              <AlertIcon />
              <Text fontSize="sm">
                <strong>Critical:</strong> Documents uploaded here will be enforced on ALL content, including personal posts. 
                Use for: Code of Conduct, Social Media Policy, Acceptable Use, Data Protection.
              </Text>
            </Alert>

            <DocumentsTable 
              documents={universalDocuments} 
              tier="universal"
              emptyMessage="No universal policies uploaded yet. Upload core company policies that must apply to all content."
              textColorSecondary={textColorSecondary}
              onUpload={openUploadModal}
              onDelete={handleDeleteDocument}
            />
          </CardBody>
        </Card>

        {/* Professional Brand & Compliance Section */}
        <Card bg={bgColor} boxShadow="lg" borderLeft="4px solid" borderColor="blue.500">
          <CardBody p={{ base: 4, md: 6 }}>
            <Flex align="center" justify="space-between" mb={4}>
              <Flex align="center" gap={3}>
                <Box p={2} bg={professionalBg} borderRadius="md">
                  <Icon as={FaBriefcase} boxSize={6} color="blue.500" />
                </Box>
                <Box>
                  <HStack>
                    <Heading size="md" color={textColor}>🟣 Professional Brand & Compliance</Heading>
                    <Badge colorScheme="blue" fontSize="sm">{professionalDocuments.length} documents</Badge>
                  </HStack>
                  <Text fontSize="sm" color="blue.500" fontWeight="600">
                    Applies ONLY to Company/Brand Posts
                  </Text>
                </Box>
              </Flex>
              <Button
                leftIcon={<Icon as={FaUpload} />}
                colorScheme="blue"
                onClick={() => openUploadModal('professional')}
                size="sm"
              >
                Upload Guidelines
              </Button>
            </Flex>

            <Alert status="info" mb={4} borderRadius="md" size="sm">
              <AlertIcon />
              <Text fontSize="sm">
                Documents here apply only when posting on behalf of the company. 
                Use for: Brand Guidelines, Tone of Voice, Product Messaging, Marketing Compliance.
              </Text>
            </Alert>

            <DocumentsTable 
              documents={professionalDocuments} 
              tier="professional"
              emptyMessage="No professional brand documents uploaded yet. Upload brand guidelines and compliance documents for official company communications."
              textColorSecondary={textColorSecondary}
              onUpload={openUploadModal}
              onDelete={handleDeleteDocument}
            />
          </CardBody>
        </Card>
      </VStack>

      {/* Upload Document Modal */}
      <Modal isOpen={isOpen} onClose={onClose} size="lg">
        <ModalOverlay 
          bg="rgba(0, 0, 0, 0.7)" 
          backdropFilter="blur(4px)"
        />
        <ModalContent bg={bgColor} shadow="2xl">
          <ModalHeader>
            <Flex align="center" gap={2}>
              <Icon 
                as={uploadTier === 'universal' ? FaShieldAlt : FaBriefcase} 
                color={uploadTier === 'universal' ? 'red.500' : 'blue.500'} 
              />
              {uploadTier === 'universal' ? '🔴 Upload Universal Policy' : '🟣 Upload Professional Brand Document'}
            </Flex>
          </ModalHeader>
          <ModalCloseButton />
          <ModalBody>
            <VStack spacing={4} align="stretch">
              <Alert 
                status={uploadTier === 'universal' ? 'warning' : 'info'} 
                borderRadius="md"
                size="sm"
              >
                <AlertIcon />
                <Text fontSize="sm">
                  {uploadTier === 'universal' 
                    ? 'This document will be enforced on ALL posts, including personal content.'
                    : 'This document will only apply to Company/Brand posts, not personal content.'}
                </Text>
              </Alert>

              <FormControl isRequired>
                <FormLabel>Document Category</FormLabel>
                <Select
                  value={selectedCategory}
                  onChange={(e) => setSelectedCategory(e.target.value)}
                >
                  {(uploadTier === 'universal' ? UNIVERSAL_POLICY_CATEGORIES : PROFESSIONAL_BRAND_CATEGORIES).map((cat) => (
                    <option key={cat.value} value={cat.value}>
                      {cat.label}
                    </option>
                  ))}
                </Select>
              </FormControl>

              <FormControl isRequired>
                <FormLabel>Select File</FormLabel>
                <Input
                  type="file"
                  accept=".pdf,.doc,.docx,.txt,.md,.xlsx,.xls,.pptx,.ppt,.csv"
                  onChange={handleFileSelect}
                />
                <Text fontSize="xs" color={textColorSecondary} mt={2}>
                  Supported formats: PDF, DOC, DOCX, TXT, MD, XLSX, PPTX, CSV
                </Text>
              </FormControl>

              {selectedFile && (
                <Box p={3} bg={selectedFileBg} borderRadius="md">
                  <Text fontSize="sm" fontWeight="600">Selected: {selectedFile.name}</Text>
                  <Text fontSize="xs" color={textColorSecondary}>
                    Size: {(selectedFile.size / 1024).toFixed(2)} KB
                  </Text>
                </Box>
              )}
            </VStack>
          </ModalBody>

          <ModalFooter>
            <Button variant="ghost" mr={3} onClick={onClose}>
              Cancel
            </Button>
            <Button
              colorScheme={uploadTier === 'universal' ? 'red' : 'blue'}
              onClick={handleUploadDocument}
              isLoading={uploading}
              leftIcon={<Icon as={FaUpload} />}
            >
              Upload
            </Button>
          </ModalFooter>
        </ModalContent>
      </Modal>
    </Box>
  );
}
