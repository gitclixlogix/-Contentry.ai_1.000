'use client';
import { useTranslation } from 'react-i18next';
import { useState } from 'react';
import { useRouter } from 'next/navigation';
import {
  Box,
  Button,
  Flex,
  FormControl,
  FormLabel,
  Heading,
  Input,
  Text,
  VStack,
  useColorModeValue,
  useToast,
  FormHelperText,
  InputGroup,
  InputRightElement,
  Icon,
  Tag,
  HStack,
  IconButton,
} from '@chakra-ui/react';
import { FaEye, FaEyeSlash, FaPlus, FaTimes, FaBuilding } from 'react-icons/fa';
import axios from 'axios';
import { getApiUrl } from '@/lib/api';

export default function EnterpriseRegisterPage() {
  const router = useRouter();
  const toast = useToast();
  const [loading, setLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  
  const [formData, setFormData] = useState({
    name: '',
    domains: [],
    admin_name: '',
    admin_email: '',
    admin_password: '',
  });
  
  const [currentDomain, setCurrentDomain] = useState('');

  const textColor = useColorModeValue('navy.700', 'white');
  const brandStars = useColorModeValue('brand.500', 'brand.400');

  const addDomain = () => {
    if (currentDomain && !formData.domains.includes(currentDomain)) {
      setFormData({ ...formData, domains: [...formData.domains, currentDomain] });
      setCurrentDomain('');
    }
  };

  const removeDomain = (domain) => {
    setFormData({
      ...formData,
      domains: formData.domains.filter((d) => d !== domain),
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (formData.domains.length === 0) {
      toast({
        title: 'Error',
        description: 'Please add at least one domain',
        status: 'error',
        duration: 3000,
      });
      return;
    }
    
    setLoading(true);
    try {
      const API = getApiUrl();
      const response = await axios.post(`${API}/enterprises`, formData);
      
      toast({
        title: 'Success!',
        description: 'Enterprise account created successfully',
        status: 'success',
        duration: 5000,
      });
      
      // Auto-login the admin
      const loginResponse = await axios.post(`${API}/auth/login`, {
        email: formData.admin_email,
        password: formData.admin_password,
      });
      
      localStorage.setItem('contentry_user', JSON.stringify(loginResponse.data.user));
      
      setTimeout(() => {
        router.push('/contentry/enterprise/dashboard');
      }, 1000);
    } catch (error) {
      toast({
        title: 'Error',
        description: error.response?.data?.detail || 'Failed to create enterprise',
        status: 'error',
        duration: 5000,
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <Flex
      minH="100vh"
      align="center"
      justify="center"
      bg={useColorModeValue('gray.50', 'gray.900')}
      px={{ base: 4, md: 0 }}
    >
      <Box
        maxW={{ base: 'full', md: '2xl' }}
        w="full"
        bg={useColorModeValue('white', 'gray.800')}
        boxShadow="2xl"
        rounded="lg"
        p={{ base: 6, md: 8 }}
      >
        <VStack spacing={6} align="stretch">
          <Box textAlign="center">
            <Flex align="center" justify="center" mb={4}>
              <Icon as={FaBuilding} boxSize={12} color="brand.500" />
            </Flex>
            <Heading color={textColor} fontSize={{ base: '28px', md: '36px' }} mb={2}>
              Enterprise Registration
            </Heading>
            <Text color="gray.500" fontSize={{ base: 'sm', md: 'md' }}>
              Create your enterprise account to manage your organization
            </Text>
          </Box>

          <form onSubmit={handleSubmit}>
            <VStack spacing={4}>
              <FormControl isRequired>
                <FormLabel color={textColor} fontSize="sm" fontWeight="500">
                  Enterprise Name<Text as="span" color={brandStars}>*</Text>
                </FormLabel>
                <Input
                  placeholder="Acme Corporation"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  size="lg"
                />
              </FormControl>

              <FormControl isRequired>
                <FormLabel color={textColor} fontSize="sm" fontWeight="500">
                  Email Domains<Text as="span" color={brandStars}>*</Text>
                </FormLabel>
                <InputGroup size="lg">
                  <Input
                    placeholder="acme.com"
                    value={currentDomain}
                    onChange={(e) => setCurrentDomain(e.target.value)}
                    onKeyPress={(e) => {
                      if (e.key === 'Enter') {
                        e.preventDefault();
                        addDomain();
                      }
                    }}
                  />
                  <InputRightElement width="4.5rem">
                    <Button h="1.75rem" size="sm" onClick={addDomain} colorScheme="brand">
                      <Icon as={FaPlus} />
                    </Button>
                  </InputRightElement>
                </InputGroup>
                <FormHelperText>
                  Enter domains without @ symbol (e.g., acme.com)
                </FormHelperText>
                {formData.domains.length > 0 && (
                  <HStack mt={2} flexWrap="wrap">
                    {formData.domains.map((domain) => (
                      <Tag
                        key={domain}
                        size="lg"
                        borderRadius="full"
                        variant="solid"
                        colorScheme="brand"
                      >
                        <Text>{domain}</Text>
                        <IconButton
                          size="xs"
                          ml={2}
                          icon={<FaTimes />}
                          onClick={() => removeDomain(domain)}
                          variant="ghost"
                          aria-label="Remove domain"
                        />
                      </Tag>
                    ))}
                  </HStack>
                )}
              </FormControl>

              <Box w="full" borderTop="1px" borderColor="gray.200" pt={4} mt={4}>
                <Text fontSize="md" fontWeight="600" color={textColor} mb={4}>
                  Administrator Account
                </Text>

                <VStack spacing={4}>
                  <FormControl isRequired>
                    <FormLabel color={textColor} fontSize="sm" fontWeight="500">
                      Admin Name<Text as="span" color={brandStars}>*</Text>
                    </FormLabel>
                    <Input
                      placeholder="John Doe"
                      value={formData.admin_name}
                      onChange={(e) => setFormData({ ...formData, admin_name: e.target.value })}
                      size="lg"
                    />
                  </FormControl>

                  <FormControl isRequired>
                    <FormLabel color={textColor} fontSize="sm" fontWeight="500">
                      Admin Email<Text as="span" color={brandStars}>*</Text>
                    </FormLabel>
                    <Input
                      type="email"
                      placeholder="admin@acme.com"
                      value={formData.admin_email}
                      onChange={(e) => setFormData({ ...formData, admin_email: e.target.value })}
                      size="lg"
                    />
                    <FormHelperText>
                      Must use one of your enterprise domains
                    </FormHelperText>
                  </FormControl>

                  <FormControl isRequired>
                    <FormLabel color={textColor} fontSize="sm" fontWeight="500">
                      Admin Password<Text as="span" color={brandStars}>*</Text>
                    </FormLabel>
                    <InputGroup size="lg">
                      <Input
                        type={showPassword ? 'text' : 'password'}
                        placeholder="Min. 8 characters"
                        value={formData.admin_password}
                        onChange={(e) => setFormData({ ...formData, admin_password: e.target.value })}
                      />
                      <InputRightElement>
                        <Icon
                          color="gray.400"
                          _hover={{ cursor: 'pointer' }}
                          as={showPassword ? FaEyeSlash : FaEye}
                          onClick={() => setShowPassword(!showPassword)}
                        />
                      </InputRightElement>
                    </InputGroup>
                  </FormControl>
                </VStack>
              </Box>

              <Button
                fontSize="sm"
                variant="brand"
                fontWeight="500"
                w="100%"
                h="50"
                type="submit"
                isLoading={loading}
                mt={4}
              >
                Create Enterprise Account
              </Button>

              <Text fontSize="sm" color="gray.500" textAlign="center">
                Already have an account?{' '}
                <Text
                  as="span"
                  color={brandStars}
                  fontWeight="500"
                  cursor="pointer"
                  onClick={() => router.push('/contentry/auth/login')}
                >
                  Sign In
                </Text>
              </Text>
            </VStack>
          </form>
        </VStack>
      </Box>
    </Flex>
  );
}
