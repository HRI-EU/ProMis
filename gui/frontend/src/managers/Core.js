import LayerManager from "./LayerManager";
import MapManager from "./MapManager";
import SourceCodeManager from "./SourceCodeManager";
import PushDownAutoComplete from "../utils/PushDownAutoCompletion";

class Core {
  //References for UI element update callbacks
  refSidebarRight = null;
  refBottomBar = null;
  toggleDrawerRight = null;

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
    this.autoComplete = new PushDownAutoComplete();
    this.autoComplete.push_list(
      this.sourceMan.locationTypes.map((loc_type) => loc_type.locationType),
    );
  }

  initCodeEditor(codeEditor) {
    this.codeEditor = codeEditor;
  }

  getCodeEditor() {
    return this.codeEditor !== undefined ? this.codeEditor : null;
  }

  //Call to access core instance
  C() {
    //Access core, will only create new instance if never called before
    return new Core();
  }

  addMapComponentCallback(callback) {
    //Set the callback for the map component
    this.mapComponentCallback = callback;
  }

  //Set the reference to the updateCallback of SidebarRight
  addRefSidebarRight(updateCallback) {
    this.refSidebarRight = updateCallback;
  }

  //Set the reference to the updateCallback of BottomBar
  addRefBottomBar(updateCallback) {
    this.refBottomBar = updateCallback;
  }

  addToggleDrawerRight(toggleCallback) {
    this.toggleDrawerRight = toggleCallback;
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

  toggleDrawerSidebarRight() {
    if (this.toggleDrawerRight != null) {
      this.toggleDrawerRight();
    }
  }

  //Call to trigger the ui refresh of BottomBar
  updateBottomBar() {
    if (this.refBottomBar != null) {
      this.refBottomBar();
    }
  }

  //Call to trigger the map component update
  updateMapComponent(entity, type = 0) {
    if (this.mapComponentCallback != null) {
      this.mapComponentCallback(entity, type);
    }
  }
}

export const C = Core.prototype.C;
