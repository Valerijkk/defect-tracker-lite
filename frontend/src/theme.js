import { createTheme } from '@mui/material/styles';

const theme = createTheme({
  palette: {
    mode: 'light',
    primary: { main: '#4f46e5' }, // indigo
    secondary: { main: '#06b6d4' }, // cyan
    success: { main: '#16a34a' },
    warning: { main: '#f59e0b' },
    error: { main: '#dc2626' },
    background: { default: '#f6f7fb' }
  },
  typography: {
    fontFamily: '"Inter", "Roboto", "Helvetica", "Arial", sans-serif',
    h4: { fontWeight: 700 },
    h5: { fontWeight: 600 }
  },
  shape: { borderRadius: 12 },
  components: {
    MuiPaper: {
      defaultProps: { elevation: 1 },
      styleOverrides: {
        root: { borderRadius: 14 }
      }
    },
    MuiButton: {
      styleOverrides: { root: { textTransform: 'none', fontWeight: 600 } }
    },
    MuiAppBar: {
      styleOverrides: { root: { borderBottom: '1px solid #e5e7eb' } }
    }
  }
});
export default theme;
