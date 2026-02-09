/**
 * Shared Components Index
 * 
 * Central export for all reusable components.
 * Import from '@/components/shared' for easy access.
 * 
 * Example:
 * import { FormModal, DataTable, FormField, ConfirmationModal } from '@/components/shared';
 */

// ============================================
// Display Components
// ============================================
export { UserInfoCell } from './display/UserInfoCell';
export { InfoRow } from './display/InfoRow';
export { ScoreBadge, ScoreIndicator } from './display/ScoreBadge';
export { StatusBadge } from './display/StatusBadge';
export { EmptyState } from './display/EmptyState';

// ============================================
// Modal Components
// ============================================
export { 
  ConfirmationModal, 
  DeleteConfirmationModal,
  ApproveConfirmationModal 
} from './modals/ConfirmationModal';

export {
  FormModal,
  CreateFormModal,
  EditFormModal
} from './modals/FormModal';

// ============================================
// Form Components
// ============================================
export {
  FormField,
  TextField,
  EmailField,
  PasswordField,
  TextareaField,
  SelectField
} from './forms/FormField';

// ============================================
// Table Components
// ============================================
export { DataTable } from './tables/DataTable';

// ============================================
// Error Handling Components
// ============================================
export { 
  GlobalErrorBoundary,
  useErrorHandler 
} from './errors/GlobalErrorBoundary';
