import React from 'react';
export function Legend() {
  return <div className="legend"><span><i className="sw hl" /> текущее состояние / действие</span><span><i className="sw cf" /> конфликт / разделитель</span><span><i className="sw nw" /> новое состояние</span><span><i className="sw group" /> класс эквивалентности</span><span><i className="sw final" /> заключительное</span><span><i className="sw initial" /> начальное</span></div>;
}
