/**
 * FormField - Unified form input wrapper with validation
 * 
 * Wraps form inputs with consistent styling, labels, help text, and error handling.
 * 
 * Props:
 * - label (string): Field label
 * - name (string): Field name for form
 * - type (string): Input type - 'text', 'email', 'password', 'textarea', 'select'
 * - value (any): Current field value
 * - onChange (function): Change handler
 * - placeholder (string): Input placeholder
 * - helpText (string): Help text below input
 * - error (string): Error message to display
 * - isRequired (boolean): Whether field is required
 * - isDisabled (boolean): Whether field is disabled
 * - isReadOnly (boolean): Whether field is read-only
 * - options (array): Options for select type [{value, label}]
 * - rows (number): Number of rows for textarea
 * - leftElement (ReactNode): Element to show on left of input
 * - rightElement (ReactNode): Element to show on right of input
 */

import React from 'react';
import {
  FormControl,
  FormLabel,
  FormHelperText,
  FormErrorMessage,
  Input,
  Textarea,
  Select,
  InputGroup,
  InputLeftElement,
  InputRightElement,
  useColorModeValue
} from '@chakra-ui/react';

export function FormField({
  label,
  name,
  type = 'text',
  value,
  onChange,
  onBlur,
  placeholder,
  helpText,
  error,
  isRequired = false,
  isDisabled = false,
  isReadOnly = false,
  options = [],
  rows = 3,
  leftElement,
  rightElement,
  size = 'md',
  autoFocus = false,
  maxLength,
  ...rest
}) {
  const errorColor = useColorModeValue('red.500', 'red.300');
  const helpColor = useColorModeValue('gray.500', 'gray.400');
  
  const hasError = Boolean(error);
  
  const handleChange = (e) => {
    if (onChange) {
      // Support both (value) and (event) patterns
      if (typeof onChange === 'function') {
        onChange(e.target?.value ?? e, e);
      }
    }
  };

  const renderInput = () => {
    const commonProps = {
      name,
      value: value ?? '',
      onChange: handleChange,
      onBlur,
      placeholder,
      isDisabled,
      isReadOnly,
      size,
      autoFocus,
      maxLength,
      ...rest
    };

    switch (type) {
      case 'textarea':
        return (
          <Textarea
            {...commonProps}
            rows={rows}
            resize="vertical"
          />
        );
      
      case 'select':
        return (
          <Select {...commonProps}>
            {placeholder && (
              <option value="" disabled>
                {placeholder}
              </option>
            )}
            {options.map((opt) => (
              <option key={opt.value} value={opt.value}>
                {opt.label}
              </option>
            ))}
          </Select>
        );
      
      default:
        if (leftElement || rightElement) {
          return (
            <InputGroup size={size}>
              {leftElement && (
                <InputLeftElement>{leftElement}</InputLeftElement>
              )}
              <Input {...commonProps} type={type} />
              {rightElement && (
                <InputRightElement>{rightElement}</InputRightElement>
              )}
            </InputGroup>
          );
        }
        return <Input {...commonProps} type={type} />;
    }
  };

  return (
    <FormControl 
      isInvalid={hasError} 
      isRequired={isRequired}
      isDisabled={isDisabled}
      isReadOnly={isReadOnly}
    >
      {label && (
        <FormLabel fontSize={size === 'sm' ? 'sm' : 'md'}>
          {label}
        </FormLabel>
      )}
      {renderInput()}
      {helpText && !hasError && (
        <FormHelperText color={helpColor}>
          {helpText}
        </FormHelperText>
      )}
      {hasError && (
        <FormErrorMessage color={errorColor}>
          {error}
        </FormErrorMessage>
      )}
    </FormControl>
  );
}

// Convenience exports for specific field types
export function TextField(props) {
  return <FormField {...props} type="text" />;
}

export function EmailField(props) {
  return <FormField {...props} type="email" />;
}

export function PasswordField(props) {
  return <FormField {...props} type="password" />;
}

export function TextareaField(props) {
  return <FormField {...props} type="textarea" />;
}

export function SelectField(props) {
  return <FormField {...props} type="select" />;
}

export default FormField;
