FROM nginx:1.15.8

RUN rm /etc/nginx/conf.d/default.conf
COPY nginx/project.conf /etc/nginx/conf.d/
CMD ["nginx", "-g", "daemon off;"]