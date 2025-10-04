import React, { useState } from 'react';
import AppBar from '@mui/material/AppBar';
import Toolbar from '@mui/material/Toolbar';
import Typography from '@mui/material/Typography';
import Box from '@mui/material/Box';
import Container from '@mui/material/Container';
import CssBaseline from '@mui/material/CssBaseline';
import Stack from '@mui/material/Stack';
import IconButton from '@mui/material/IconButton';
import Tooltip from '@mui/material/Tooltip';
import Avatar from '@mui/material/Avatar';
import Menu from '@mui/material/Menu';
import MenuItem from '@mui/material/MenuItem';
import Divider from '@mui/material/Divider';

function initialsFromEmail(email) {
  if (!email) return 'U';
  const name = email.split('@')[0];
  const parts = name.replace(/[._-]+/g, ' ').trim().split(/\s+/);
  const letters = (parts[0]?.[0] || 'U') + (parts[1]?.[0] || '');
  return letters.toUpperCase();
}

export default function AppLayout({
                                    title,
                                    subtitle,
                                    actions,
                                    children,
                                    onLogout,
                                    onProfile,
                                    userEmail,
                                    themeMode = 'light',
                                    onToggleTheme,
                                  }) {
  const [anchorEl, setAnchorEl] = useState(null);
  const open = Boolean(anchorEl);
  const handleOpen = (e) => setAnchorEl(e.currentTarget);
  const handleClose = () => setAnchorEl(null);

  return (
      <Box sx={{
        minHeight: '100vh',
        background:
            'radial-gradient(1200px 600px at 10% -10%, rgba(79,70,229,0.08), transparent), radial-gradient(1000px 500px at 100% -10%, rgba(6,182,212,0.15), transparent)'
      }}>
        <CssBaseline />
        <AppBar position="sticky" color="inherit" elevation={0} sx={{ backdropFilter: 'blur(6px)' }}>
          <Toolbar sx={{ gap: 2 }}>
            <Typography variant="h6" sx={{ fontWeight: 700, flexGrow: 1 }}>
              {title || 'Defect Tracker Lite'}
            </Typography>

            {subtitle && (
                <Typography variant="body2" color="text.secondary" sx={{ mr: 2 }}>
                  {subtitle}
                </Typography>
            )}
            {actions && <Stack direction="row" spacing={1}>{actions}</Stack>}

            {/* переключатель темы (эмодзи) */}
            <Tooltip title={`Сменить тему: ${themeMode === 'dark' ? 'светлая' : 'тёмная'}`}>
              <IconButton
                  size="small"
                  onClick={onToggleTheme}
                  aria-label="Сменить тему"
                  sx={{ fontSize: 18 }}
              >
                {themeMode === 'dark' ? '🌙' : '☀️'}
              </IconButton>
            </Tooltip>

            {/* профиль */}
            <Tooltip title={userEmail || 'Аккаунт'}>
              <IconButton onClick={handleOpen} size="small" sx={{ ml: 0.5 }}>
                <Avatar sx={{ width: 32, height: 32 }}>{initialsFromEmail(userEmail)}</Avatar>
              </IconButton>
            </Tooltip>
            <Menu
                anchorEl={anchorEl}
                open={open}
                onClose={handleClose}
                onClick={handleClose}
                transformOrigin={{ horizontal: 'right', vertical: 'top' }}
                anchorOrigin={{ horizontal: 'right', vertical: 'bottom' }}
            >
              <MenuItem disabled sx={{ opacity: 1 }}>
                <Typography variant="body2">{userEmail || 'user@local'}</Typography>
              </MenuItem>
              <Divider />
              <MenuItem onClick={() => onProfile && onProfile()}>Профиль</MenuItem>
              <MenuItem onClick={() => onLogout && onLogout()}>Выйти</MenuItem>
            </Menu>
          </Toolbar>
        </AppBar>

        <Container maxWidth="lg" sx={{ py: 3 }}>
          {children}
        </Container>

        <Box component="footer" sx={{ textAlign: 'center', py: 3, color: 'text.secondary' }}>
          <Typography variant="caption">Made with MUI • Demo</Typography>
        </Box>
      </Box>
  );
}
