import { useEffect } from 'react';
import { Box, Typography } from '@mui/material';

const Navigation: React.FC = () => {

    return (
        <Box sx={{ position: 'fixed', overflow: 'hidden', width: '100%', backgroundColor: 'blue' }}>
            <Typography variant="h2">THIS WILL BE NAVIGATION</Typography>
        </Box>
    );
};

export default Navigation;
