import { codes } from 'micromark-util-symbol/codes.js';
import { addRemarkExtension, assert } from './helpers';


function templateVariableSyntax() {
  return {
    text: {
      [codes.leftCurlyBrace]: {
        tokenize: tokenizeTemplateVariable,
      },
    }
  };

  function tokenizeTemplateVariable(effects, ok, nok) {
    let closeBraceCount = 0;
    return start;

    function start(code) {
      assert(code === codes.leftCurlyBrace, 'expected `{`}');
      effects.enter('templateVariable');
      effects.consume(code);
      return start2;
    }
    function start2(code) {
      if (code !== codes.leftCurlyBrace) {
        return nok(code);
      }
      effects.consume(code);
      return between;
    }
    function between(code) {
      if (code === codes.eof) {
        return nok(code);
      } else if (code === codes.rightCurlyBrace) {
        // Closing sequence or part of content?
        closeBraceCount = 0;
        return sequenceClose(code);
      } else {
        effects.consume(code);
        return between;
      }
    }
    function sequenceClose(code) {
      if (code === codes.rightCurlyBrace) {
        effects.consume(code);
        closeBraceCount += 1;

        if (closeBraceCount === 2) {
          // Dummy close events, rewritten in resolveTemplateVariable
          effects.exit('templateVariable');
          return ok(code);
        } else {
          return sequenceClose;
        }
      } else {
        return between(code);
      }
    }
  }

}


function templateVariableFromMarkdown() {
  return {
    enter: {
      templateVariable: enterTemplateVariable,
    },
    exit: {
      templateVariable: exitTemplateVariable,
    }
  };

  function enterTemplateVariable(token) {
    this.enter({type: 'templateVariable', value: ''}, token);
  }
  function exitTemplateVariable(token) {
    const node = this.stack[this.stack.length - 1];
    node.value = this.sliceSerialize(token); 
    this.exit(token);
  }
}

function templateVariableToMarkdown() {
  return {
    handlers: {
      templateVariable,
    } 
  };

  function templateVariable(node, _, context) {
    const exit = context.enter('templateVariable');
    const value = node.value;
    exit();
    return value;
  }
}


export function remarkTemplateVariables() {
  addRemarkExtension(this, templateVariableSyntax(), templateVariableFromMarkdown(), templateVariableToMarkdown());
}
