'use client';
import { Button, Icon, Tooltip } from '@chakra-ui/react';
import { FaFileAlt } from 'react-icons/fa';
import { useRouter } from 'next/navigation';

/**
 * Reusable Print Report Button component
 * Opens the report page for the current user or specified user
 * @param {string} userId - Optional user ID to generate report for
 * @param {string} size - Button size (default: 'md')
 * @param {string} variant - Button variant (default: 'solid')
 * @param {boolean} iconOnly - Show only icon without text
 * @param {string} colorScheme - Button color scheme (default: 'blue')
 */
export default function PrintReportButton({ 
  userId, 
  size = 'md', 
  variant = 'solid',
  iconOnly = false,
  colorScheme = 'blue',
  label = 'View Report'
}) {
  const router = useRouter();

  const handleClick = () => {
    // Get user from localStorage if not provided
    let targetUserId = userId;
    if (!targetUserId) {
      const savedUser = localStorage.getItem('contentry_user');
      if (savedUser) {
        const userData = JSON.parse(savedUser);
        targetUserId = userData.id;
      }
    }
    
    // Open report in new tab
    const reportUrl = targetUserId 
      ? `/contentry/report?user_id=${targetUserId}`
      : '/contentry/report';
    window.open(reportUrl, '_blank');
  };

  if (iconOnly) {
    return (
      <Tooltip label={label}>
        <Button
          onClick={handleClick}
          colorScheme={colorScheme}
          size={size}
          variant={variant}
        >
          <Icon as={FaFileAlt} />
        </Button>
      </Tooltip>
    );
  }

  return (
    <Button
      leftIcon={<Icon as={FaFileAlt} />}
      onClick={handleClick}
      colorScheme={colorScheme}
      size={size}
      variant={variant}
    >
      {label}
    </Button>
  );
}
