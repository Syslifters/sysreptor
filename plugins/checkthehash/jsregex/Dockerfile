FROM ruby
WORKDIR /usr/src/app
RUN gem install js_regex json
COPY . .
CMD [ "ruby", "index.rb" ]