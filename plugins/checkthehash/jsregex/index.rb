require 'json'
require 'js_regex'

# Read the JSON file
file_path = 'prototypes.json'
file_content = File.read(file_path)
prototypes = JSON.parse(file_content)

# Convert each regex to JavaScript-compatible regex and store as a hash
prototypes.each do |prototype|
  ruby_regex = Regexp.new(prototype['regex'], Regexp::IGNORECASE)
  js_regex = JsRegex.new(ruby_regex)
  prototype['regex'] = js_regex.to_h
end

# Print the updated JSON
puts JSON.pretty_generate(prototypes)