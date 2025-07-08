import { Box, CssBaseline } from '@mui/material';
import { AppProps } from 'next/app';
import Head from 'next/head';
import { useEffect } from 'react';

// App
const App = ({ Component, pageProps }: AppProps) => {

    return (
        <Box>
            <Head>
                <title>CSC 4350 Project</title>
                <meta name="viewport" content="initial-scale=1.0, width=device-width" />
            </Head>
            <CssBaseline />
            <Component {...pageProps} />
        </Box>
    );
};

export default App;
