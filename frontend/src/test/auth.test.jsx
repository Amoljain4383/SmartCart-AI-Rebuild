import React from 'react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import Login from '../pages/Login';
import Register from '../pages/Register';
import { authApi } from '../api/auth';
import { AuthProvider } from '../context/AuthContext';

vi.mock('../api/auth', () => ({
  authApi: {
    login: vi.fn(),
    register: vi.fn(),
    getProfile: vi.fn(),
    logout: vi.fn(),
  },
}));

describe('Auth Pages & Security', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.clear();
  });

  it('submits login form with user entered email and password', async () => {
    authApi.login.mockResolvedValueOnce({
      access_token: 'fake-jwt-token',
      token_type: 'bearer',
      user: { id: 'u1', email: 'test@example.com', role: 'user', full_name: 'Test User' },
    });

    render(
      <AuthProvider>
        <BrowserRouter>
          <Login />
        </BrowserRouter>
      </AuthProvider>
    );

    const emailInput = screen.getByPlaceholderText('name@example.com');
    const passwordInput = screen.getByPlaceholderText('••••••••');
    const submitBtn = screen.getByRole('button', { name: /sign in/i });

    fireEvent.change(emailInput, { target: { value: 'user@example.com' } });
    fireEvent.change(passwordInput, { target: { value: 'SecurePass123!' } });
    fireEvent.click(submitBtn);

    await waitFor(() => {
      expect(authApi.login).toHaveBeenCalledWith('user@example.com', 'SecurePass123!');
    });
  });

  it('registration submits full_name, email, password and does not send an admin role', async () => {
    authApi.register.mockResolvedValueOnce({
      access_token: 'fake-jwt-token',
      token_type: 'bearer',
      user: { id: 'u2', email: 'new@example.com', role: 'user', full_name: 'New User' },
    });

    render(
      <AuthProvider>
        <BrowserRouter>
          <Register />
        </BrowserRouter>
      </AuthProvider>
    );

    const nameInput = screen.getByPlaceholderText(/e\.g\. Priya Sharma/i);
    const emailInput = screen.getByPlaceholderText('name@example.com');
    const passwordInput = screen.getByPlaceholderText('••••••••');
    const registerBtn = screen.getByRole('button', { name: /register & continue/i });

    fireEvent.change(nameInput, { target: { value: 'Alice Smith' } });
    fireEvent.change(emailInput, { target: { value: 'alice@example.com' } });
    fireEvent.change(passwordInput, { target: { value: 'ValidPass123!' } });
    fireEvent.click(registerBtn);

    await waitFor(() => {
      expect(authApi.register).toHaveBeenCalledWith('alice@example.com', 'ValidPass123!', 'Alice Smith');
    });

    // Verify registration arguments contain strictly 3 items (email, password, full_name), no role
    const callArgs = authApi.register.mock.calls[0];
    expect(callArgs.length).toBe(3);
    expect(callArgs).not.toContain('admin');
  });
});
