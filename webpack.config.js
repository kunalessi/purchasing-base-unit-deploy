const path = require('path');

module.exports = {
    entry: './Client/main.js',
    output: {
        filename: 'bundle.js',
        path: path.resolve(__dirname, 'Client/dist'),
        clean: true
    },
    mode: 'production',
    module: {
        rules: [
            {
                test: /\.js$/,
                exclude: /node_modules/,
                use: {
                    loader: 'babel-loader',
                    options: {
                        presets: ['@babel/preset-env']
                    }
                }
            }
        ]
    }
};