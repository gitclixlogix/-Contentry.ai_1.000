'use client';
import React, { useState } from 'react';
import { ComposableMap, Geographies, Geography, Marker, ZoomableGroup } from 'react-simple-maps';
import { 
  Box, 
  useColorModeValue, 
  VStack, 
  Text, 
  Badge, 
  HStack,
  Stat,
  StatLabel,
  StatNumber,
  StatGroup,
  Card,
  CardBody
} from '@chakra-ui/react';
import { FaMale, FaFemale, FaUsers } from 'react-icons/fa';

// Using a reliable world map TopoJSON
const geoUrl = "https://cdn.jsdelivr.net/npm/world-atlas@2/countries-110m.json";

export default function WorldMap({ data = {}, countryDetails = {}, height = "400px" }) {
  const [selectedCountry, setSelectedCountry] = useState(null);
  
  const fillColor = useColorModeValue('#E5E7EB', '#2D3748');
  const hoverColor = useColorModeValue('#1e40af', '#60a5fa');
  const markerColor = '#1e40af';
  const textColor = useColorModeValue('#1A202C', '#F7FAFC');
  const cardBg = useColorModeValue('white', 'gray.800');
  const strokeColor = useColorModeValue('#FFFFFF', '#1A202C');

  // Convert country data to markers with coordinates
  const markers = [
    { name: "United States", coordinates: [-95.7129, 37.0902], users: data["United States"] || 450 },
    { name: "United Kingdom", coordinates: [-3.4360, 55.3781], users: data["United Kingdom"] || 320 },
    { name: "Canada", coordinates: [-106.3468, 56.1304], users: data["Canada"] || 180 },
    { name: "Germany", coordinates: [10.4515, 51.1657], users: data["Germany"] || 150 },
    { name: "Australia", coordinates: [133.7751, -25.2744], users: data["Australia"] || 100 },
    { name: "France", coordinates: [2.2137, 46.2276], users: data["France"] || 90 },
    { name: "India", coordinates: [78.9629, 20.5937], users: data["India"] || 80 },
    { name: "Brazil", coordinates: [-51.9253, -14.2350], users: data["Brazil"] || 70 },
    { name: "Japan", coordinates: [138.2529, 36.2048], users: data["Japan"] || 60 },
    { name: "Spain", coordinates: [-3.7492, 40.4637], users: data["Spain"] || 50 },
  ];

  const handleMarkerClick = (country) => {
    setSelectedCountry(country);
  };

  return (
    <Box w="100%">
      {selectedCountry && countryDetails[selectedCountry] && (
        <Card 
          mb={4} 
          bg={cardBg} 
          borderWidth="2px" 
          borderColor="brand.500"
        >
          <CardBody>
            <VStack align="start" spacing={3}>
              <HStack justify="space-between" w="100%">
                <Text fontSize="lg" fontWeight="700" color={textColor}>
                  {selectedCountry}
                </Text>
                <Badge colorScheme="brand" fontSize="md" px={3} py={1}>
                  <HStack spacing={1}>
                    <FaUsers />
                    <Text>{countryDetails[selectedCountry].total || countryDetails[selectedCountry].count || 0} Users</Text>
                  </HStack>
                </Badge>
              </HStack>
              
              {/* Show demographic breakdown if available */}
              {countryDetails[selectedCountry].male !== undefined ? (
                <StatGroup w="100%" gap={4}>
                  <Stat>
                    <StatLabel color="blue.500" fontSize="sm" fontWeight="600">
                      <HStack spacing={1}>
                        <FaMale />
                        <Text>Male</Text>
                      </HStack>
                    </StatLabel>
                    <StatNumber fontSize="2xl" color={textColor}>
                      {countryDetails[selectedCountry].male}
                    </StatNumber>
                    <Text fontSize="xs" color="gray.500">
                      {((countryDetails[selectedCountry].male / (countryDetails[selectedCountry].total || 1)) * 100).toFixed(1)}%
                    </Text>
                  </Stat>
                  
                  <Stat>
                    <StatLabel color="pink.500" fontSize="sm" fontWeight="600">
                      <HStack spacing={1}>
                        <FaFemale />
                        <Text>Female</Text>
                      </HStack>
                    </StatLabel>
                    <StatNumber fontSize="2xl" color={textColor}>
                      {countryDetails[selectedCountry].female}
                    </StatNumber>
                    <Text fontSize="xs" color="gray.500">
                      {((countryDetails[selectedCountry].female / (countryDetails[selectedCountry].total || 1)) * 100).toFixed(1)}%
                    </Text>
                  </Stat>
                  
                  {countryDetails[selectedCountry].other > 0 && (
                    <Stat>
                      <StatLabel color="blue.600" fontSize="sm" fontWeight="600">
                        Other
                      </StatLabel>
                      <StatNumber fontSize="2xl" color={textColor}>
                        {countryDetails[selectedCountry].other}
                      </StatNumber>
                      <Text fontSize="xs" color="gray.500">
                        {((countryDetails[selectedCountry].other / (countryDetails[selectedCountry].total || 1)) * 100).toFixed(1)}%
                      </Text>
                    </Stat>
                  )}
                </StatGroup>
              ) : (
                /* Show count and percentage if demographic breakdown not available */
                <HStack spacing={6}>
                  <Stat>
                    <StatLabel color="brand.500" fontSize="sm" fontWeight="600">
                      Total Users
                    </StatLabel>
                    <StatNumber fontSize="2xl" color={textColor}>
                      {countryDetails[selectedCountry].count || countryDetails[selectedCountry].total || 0}
                    </StatNumber>
                  </Stat>
                  {countryDetails[selectedCountry].percentage !== undefined && (
                    <Stat>
                      <StatLabel color="gray.500" fontSize="sm" fontWeight="600">
                        % of Total
                      </StatLabel>
                      <StatNumber fontSize="2xl" color={textColor}>
                        {countryDetails[selectedCountry].percentage.toFixed(1)}%
                      </StatNumber>
                    </Stat>
                  )}
                </HStack>
              )}
            </VStack>
          </CardBody>
        </Card>
      )}
      
      <Box w="100%" h={height} position="relative">
        <ComposableMap
          projection="geoMercator"
          projectionConfig={{
            scale: 147
          }}
          style={{
            width: "100%",
            height: "100%"
          }}
        >
          <ZoomableGroup center={[0, 20]} zoom={1}>
            <Geographies geography={geoUrl}>
              {({ geographies }) =>
                geographies.map((geo) => (
                  <Geography
                    key={geo.rsmKey}
                    geography={geo}
                    fill={fillColor}
                    stroke={strokeColor}
                    strokeWidth={0.5}
                    style={{
                      default: { outline: 'none' },
                      hover: { fill: hoverColor, outline: 'none', cursor: 'pointer' },
                      pressed: { outline: 'none' }
                    }}
                  />
                ))
              }
            </Geographies>
            
            {markers.map(({ name, coordinates, users }) => (
              <Marker key={name} coordinates={coordinates}>
                <g
                  onClick={() => handleMarkerClick(name)}
                  style={{ cursor: 'pointer' }}
                >
                  <circle 
                    r={Math.sqrt(users) / 2} 
                    fill={selectedCountry === name ? '#F158C0' : markerColor} 
                    fillOpacity={0.8}
                    stroke={selectedCountry === name ? '#6E49F5' : "#FFFFFF"}
                    strokeWidth={selectedCountry === name ? 3 : 1}
                  />
                  <title>{`${name}: ${users} users - Click for details`}</title>
                </g>
              </Marker>
            ))}
          </ZoomableGroup>
        </ComposableMap>
      </Box>
    </Box>
  );
}
