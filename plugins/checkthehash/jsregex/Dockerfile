FROM ruby
WORKDIR /usr/src/app
COPY . .
RUN gem install js_regex json
CMD [ "ruby", "index.rb" ]