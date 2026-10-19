import { render,screen,fireEvent } from '@testing-library/react';
import HeatmapViewer from '../HeatmapViewer';

test('overlay visibility and comparison controls work without changing the input',()=>{
  const result={original_image:'data:image/png;base64,a',heatmap_image:'data:image/png;base64,b'};
  render(<HeatmapViewer result={result}/>);
  fireEvent.change(screen.getByRole('slider',{name:'Overlay visibility'}),{target:{value:'35'}});
  expect(screen.getByAltText('CAM overlay')).toHaveStyle({opacity:'0.35'});
  fireEvent.click(screen.getByRole('button',{name:'Compare'}));
  expect(screen.getByAltText('Model input')).toHaveAttribute('src',result.original_image);
  expect(screen.getByAltText('CAM overlay')).toHaveAttribute('src',result.heatmap_image);
});
