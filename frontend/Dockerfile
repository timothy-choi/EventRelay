FROM node:20-alpine

WORKDIR /app

COPY frontend/package.json /app/package.json
COPY frontend/tsconfig.json /app/tsconfig.json
COPY frontend/next.config.ts /app/next.config.ts
COPY frontend/next-env.d.ts /app/next-env.d.ts

RUN npm install

COPY frontend /app

EXPOSE 3000

CMD ["npm", "run", "dev"]
