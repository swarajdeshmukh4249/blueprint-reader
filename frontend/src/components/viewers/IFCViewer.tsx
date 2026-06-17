interface IFCViewerProps {
  file?: File;
  width?: number;
  height?: number;
}

const IFCViewer = ({ width = 800, height = 600 }: IFCViewerProps) => {
  return (
    <div style={{ width, height, display: 'flex', alignItems: 'center', justifyContent: 'center', background: '#f0f0f0' }}>
      IFC Viewer coming soon
    </div>
  );
};

export default IFCViewer;