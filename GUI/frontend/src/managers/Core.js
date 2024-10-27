import LayerManager from "./LayerManager";
import MapManager from "./MapManager";
import SourceCodeManager from "./SourceCodeManager";

class Core {
  //References for UI element update callbacks
  refSidebarRight = null;
  refBottomBar = null;

  //Creates new Core if never called before, otherwise return instance (Singleton)
  constructor() {
    if (Core._instance) {
      return Core._instance;
    }

    this.init();

    Core._instance = this;
    return Core._instance;
  }

  //Initialize core
  init() {
    this.layerMan = new LayerManager();
    this.mapMan = new MapManager();
    this.sourceMan = new SourceCodeManager();
  }

  //Call to access core instance
  C() {
    //Access core, will only create new instance if never called before
    return new Core();
  }

  //Set the reference to the updateCallback of SidebarRight
  addRefSidebarRight(updateCallback) {
    this.refSidebarRight = updateCallback;
  }

  //Set the reference to the updateCallback of BottomBar
  addRefBottomBar(updateCallback) {
    this.refBottomBar = updateCallback;
  }

  //Call to trigger full ui refresh
  updateFullUI() {
    this.updateSidebarRight();
    this.updateBottomBar();
  }

  //Call to trigger the ui refresh of SidebarRight
  updateSidebarRight() {
    if (this.refSidebarRight != null) {
      this.refSidebarRight();
    }
  }

  //Call to trigger the ui refresh of BottomBar
  updateBottomBar() {
    if (this.refBottomBar != null) {
      this.refBottomBar();
    }
  }
}

export const C = Core.prototype.C;
