import { fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import { Input } from './Input';

describe('Input', () => {
  it('associates its label and forwards native input attributes', () => {
    const onChange = vi.fn();
    render(
      <Input
        label="Email address"
        name="email"
        autoComplete="email"
        value=""
        onChange={onChange}
      />,
    );

    const input = screen.getByLabelText('Email address');
    expect(input).toHaveAttribute('name', 'email');
    expect(input).toHaveAttribute('autocomplete', 'email');
    fireEvent.change(input, { target: { value: 'user@example.com' } });
    expect(onChange).toHaveBeenCalledOnce();
  });
});
